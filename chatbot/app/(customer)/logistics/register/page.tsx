"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, PackageCheck, Truck, ShieldCheck, AlertCircle, CheckCircle2, Loader2, ArrowRight } from "lucide-react";
import { apiClient } from "@/lib/api-client";

export default function CustomerShipmentRegistrationPage() {
  const router = useRouter();

  // Authentication check & prefill
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(true);
  const [authLoading, setAuthLoading] = useState<boolean>(true);

  // Form Fields state (12 fields)
  const [formData, setFormData] = useState({
    customerEmail: "",
    customerName: "",
    shipperName: "",
    recipientName: "",
    cargoDescription: "",
    deliveryType: "Standard Road Freight",
    originCity: "",
    destinationCity: "",
    weight: "",
    estimatedCost: "",
    pickupDate: new Date().toISOString().split("T")[0],
    expectedDeliveryDate: new Date(Date.now() + 86400000 * 3).toISOString().split("T")[0],
  });

  // UI & Validation state
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [successResult, setSuccessResult] = useState<any | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function checkAuthAndPrefill() {
      setAuthLoading(true);
      try {
        /**
         * The session now lives in an httpOnly cookie, so authentication is
         * resolved from the backend rather than from localStorage. The backend
         * also requires a signed-in customer for POST /shipments.
         */
        const meRes = await apiClient.getCustomerMe();
        if (cancelled) return;

        if (meRes && meRes.authenticated && meRes.user) {
          const currentUser = meRes.user;
          setIsAuthenticated(true);
          setFormData((prev) => ({
            ...prev,
            customerEmail: currentUser.email || prev.customerEmail,
            customerName:
              currentUser.full_name || currentUser.name || prev.customerName,
          }));
        } else {
          setIsAuthenticated(false);
        }
      } catch (err: any) {
        if (cancelled) return;
        // Unauthenticated (or the check failed) — the existing error banner and
        // the disabled submit button cover this; no console dump in production.
        setIsAuthenticated(false);
        setSubmitError(null);
      } finally {
        if (!cancelled) setAuthLoading(false);
      }
    }

    checkAuthAndPrefill();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // Clear field-specific error on change
    if (errors[name]) {
      setErrors((prev) => {
        const copy = { ...prev };
        delete copy[name];
        return copy;
      });
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    // 1. Customer Email
    if (!formData.customerEmail.trim()) {
      newErrors.customerEmail = "Customer Email is required.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.customerEmail.trim())) {
      newErrors.customerEmail = "Please enter a valid email address.";
    }

    // 2. Customer Name / Entity
    if (!formData.customerName.trim()) {
      newErrors.customerName = "Customer Name / Entity is required.";
    }

    // 3. Shipper Name
    if (!formData.shipperName.trim()) {
      newErrors.shipperName = "Shipper Name is required.";
    }

    // 4. Recipient Name
    if (!formData.recipientName.trim()) {
      newErrors.recipientName = "Recipient Name is required.";
    }

    // 5. Cargo Description / Package
    if (!formData.cargoDescription.trim()) {
      newErrors.cargoDescription = "Cargo Description / Package is required.";
    }

    // 6. Delivery Type
    if (!formData.deliveryType.trim()) {
      newErrors.deliveryType = "Delivery Type is required.";
    }

    // 7. Origin City / Hub
    if (!formData.originCity.trim()) {
      newErrors.originCity = "Origin City / Hub is required.";
    }

    // 8. Destination City / Hub
    if (!formData.destinationCity.trim()) {
      newErrors.destinationCity = "Destination City / Hub is required.";
    }

    // 9. Weight (kg)
    const weightNum = parseFloat(formData.weight);
    if (!formData.weight || isNaN(weightNum)) {
      newErrors.weight = "Weight (kg) is required.";
    } else if (weightNum <= 0) {
      newErrors.weight = "Weight must be greater than 0 kg.";
    }

    // 10. Estimated Cost (₹)
    if (formData.estimatedCost) {
      const costNum = parseFloat(formData.estimatedCost);
      if (isNaN(costNum) || costNum < 0) {
        newErrors.estimatedCost = "Estimated Cost must be 0 or greater.";
      }
    }

    // 11. Pickup Date
    if (!formData.pickupDate) {
      newErrors.pickupDate = "Pickup Date is required.";
    }

    // 12. Expected Delivery Date
    if (!formData.expectedDeliveryDate) {
      newErrors.expectedDeliveryDate = "Expected Delivery Date is required.";
    } else if (formData.pickupDate && formData.expectedDeliveryDate < formData.pickupDate) {
      newErrors.expectedDeliveryDate = "Expected Delivery Date cannot be before Pickup Date.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);

    // Shipment registration requires an authenticated customer on the backend.
    if (!isAuthenticated) {
      router.push(`/login?next=${encodeURIComponent("/logistics/register")}`);
      return;
    }

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = {
        customer_email: formData.customerEmail.trim(),
        customer_name: formData.customerName.trim(),
        shipper_name: formData.shipperName.trim(),
        recipient_name: formData.recipientName.trim(),
        package_name: formData.cargoDescription.trim(),
        delivery_type: formData.deliveryType,
        origin: formData.originCity.trim(),
        destination: formData.destinationCity.trim(),
        weight_kg: parseFloat(formData.weight),
        cost_inr: formData.estimatedCost ? parseFloat(formData.estimatedCost) : 0,
        pickup_date: formData.pickupDate,
        expected_delivery_date: formData.expectedDeliveryDate,
      };

      // Send request to FastAPI backend
      const res = await apiClient.post<any>("/shipments", payload);

      if (res && (res.success || res.shipment)) {
        setSuccessResult(res.shipment || res);
      } else {
        throw new Error(res.message || "Failed to register shipment in backend");
      }
    } catch (err: any) {
      // Surfaced through the existing inline error banner; nothing is dumped to
      // the production console.
      setSubmitError(err.message || "An error occurred while registering shipment. Please verify FastAPI backend is live.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto w-full px-4 sm:px-6 py-8 space-y-6">
      <Link href="/logistics" className="inline-flex items-center text-xs text-sky-400 hover:text-sky-300 transition-colors space-x-1">
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Logistics Hub</span>
      </Link>

      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Truck className="w-6 h-6 text-sky-400" />
            <span>Customer Shipment Registration Form</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Register your freight & courier consignment directly into Travelogix PostgreSQL Core
          </p>
        </div>
      </div>

      {!isAuthenticated && !authLoading && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
            <span>
              Shipment registration now requires a signed-in customer account, so this form is disabled until you sign in.
            </span>
          </div>
          <Link
            href="/login?next=%2Flogistics%2Fregister"
            className="shrink-0 px-3.5 py-2 rounded-lg bg-amber-500/20 border border-amber-500/30 font-semibold text-amber-100 hover:bg-amber-500/30 transition-colors text-center"
          >
            Sign In to Register
          </Link>
        </div>
      )}

      {/* SUCCESS CARD */}
      {successResult ? (
        <div className="bg-slate-900 border border-emerald-500/30 rounded-2xl p-8 space-y-6 text-center shadow-xl">
          <div className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-8 h-8" />
          </div>

          <div>
            <h2 className="text-xl font-bold text-white">Shipment registered successfully.</h2>
            <p className="text-xs text-slate-400 mt-1">Consignment state saved in PostgreSQL database & milestone tracking initiated.</p>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 max-w-md mx-auto space-y-2 text-left">
            <div className="text-xs text-slate-400">Tracking ID:</div>
            <div className="text-xl font-mono font-bold text-sky-400 tracking-wider">
              {successResult.tracking_id}
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs text-slate-300 pt-3 border-t border-slate-900">
              <div><span className="text-slate-500">Route:</span> {successResult.origin} &rarr; {successResult.destination}</div>
              <div><span className="text-slate-500">Status:</span> <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-bold">REGISTERED</span></div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <Link
              href="/shipments"
              className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-all inline-flex items-center justify-center space-x-2"
            >
              <span>View Shipment</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
            <Link
              href={`/logistics`}
              className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white text-xs font-semibold shadow-md shadow-sky-500/20 transition-all inline-flex items-center justify-center space-x-2"
            >
              <Truck className="w-3.5 h-3.5" />
              <span>Track Shipment</span>
            </Link>
          </div>
        </div>
      ) : (
        /* REGISTRATION FORM */
        <form onSubmit={handleSubmit} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
          {submitError && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
              <span>{submitError}</span>
            </div>
          )}

          {/* Section 1: Customer Authentication Details */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-sky-400 uppercase tracking-wider border-b border-slate-800 pb-2">
              1. Customer Information
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="customerEmail" className="block text-xs font-medium text-slate-300 mb-1">
                  Customer Email <span className="text-rose-400">*</span>
                </label>
                <input
                  type="email"
                  name="customerEmail"
                  id="customerEmail"
                  value={formData.customerEmail}
                  onChange={handleChange}
                  placeholder="e.g. customer@example.com"
                  className={`w-full px-3.5 py-2.5 bg-slate-950 border ${
                    errors.customerEmail ? "border-rose-500 focus:ring-rose-500" : "border-slate-800 focus:ring-sky-500"
                  } rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2`}
                />
                {errors.customerEmail && <p className="mt-1 text-[11px] text-rose-400">{errors.customerEmail}</p>}
              </div>

              <div>
                <label htmlFor="customerName" className="block text-xs font-medium text-slate-300 mb-1">
                  Customer Name / Entity <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  name="customerName"
                  id="customerName"
                  value={formData.customerName}
                  onChange={handleChange}
                  placeholder="e.g. Acme Corp / John Doe"
                  className={`w-full px-3.5 py-2.5 bg-slate-950 border ${
                    errors.customerName ? "border-rose-500 focus:ring-rose-500" : "border-slate-800 focus:ring-sky-500"
                  } rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2`}
                />
                {errors.customerName && <p className="mt-1 text-[11px] text-rose-400">{errors.customerName}</p>}
              </div>
            </div>
          </div>

          {/* Section 2: Parties (Shipper & Recipient) */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-sky-400 uppercase tracking-wider border-b border-slate-800 pb-2">
              2. Shipper & Recipient Details
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="shipperName" className="block text-xs font-medium text-slate-300 mb-1">
                  Shipper Name <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  name="shipperName"
                  id="shipperName"
                  value={formData.shipperName}
                  onChange={handleChange}
                  placeholder="e.g. Bangalore Warehouse Facility"
                  className={`w-full px-3.5 py-2.5 bg-slate-950 border ${
                    errors.shipperName ? "border-rose-500 focus:ring-rose-500" : "border-slate-800 focus:ring-sky-500"
                  } rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2`}
                />
                {errors.shipperName && <p className="mt-1 text-[11px] text-rose-400">{errors.shipperName}</p>}
              </div>

              <div>
                <label htmlFor="recipientName" className="block text-xs font-medium text-slate-300 mb-1">
                  Recipient Name <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  name="recipientName"
                  id="recipientName"
                  value={formData.recipientName}
                  onChange={handleChange}
                  placeholder="e.g. Goa Distribution Hub"
                  className={`w-full px-3.5 py-2.5 bg-slate-950 border ${
                    errors.recipientName ? "border-rose-500 focus:ring-rose-500" : "border-slate-800 focus:ring-sky-500"
                  } rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2`}
                />
                {errors.recipientName && <p className="mt-1 text-[11px] text-rose-400">{errors.recipientName}</p>}
              </div>
            </div>
          </div>

          {/* Section 3: Cargo & Service Type */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-sky-400 uppercase tracking-wider border-b border-slate-800 pb-2">
              3. Cargo & Freight Service
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="cargoDescription" className="block text-xs font-medium text-slate-300 mb-1">
                  Cargo Description / Package <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  name="cargoDescription"
                  id="cargoDescription"
                  value={formData.cargoDescription}
                  onChange={handleChange}
                  placeholder="e.g. Electronics & Spare Parts Box"
                  className={`w-full px-3.5 py-2.5 bg-slate-950 border ${
                    errors.cargoDescription ? "border-rose-500 focus:ring-rose-500" : "border-slate-800 focus:ring-sky-500"
                  } rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2`}
                />
                {errors.cargoDescription && <p className="mt-1 text-[11px] text-rose-400">{errors.cargoDescription}</p>}
              </div>

              <div>
                <label htmlFor="originCity" className="block text-xs font-medium text-slate-300 mb-1">
                  Delivery Type <span className="text-rose-400">*</span>
                </label>
                <select
                  name="deliveryType"
                  value={formData.deliveryType}
                  onChange={handleChange}
                  className={`w-full px-3.5 py-2.5 bg-slate-950 border ${
                    errors.deliveryType ? "border-rose-500 focus:ring-rose-500" : "border-slate-800 focus:ring-sky-500"
                  } rounded-xl text-xs text-white focus:outline-none focus:ring-2`}
                >
                  <option value="Standard Road Freight">Standard Road Freight</option>
                  <option value="Express Priority">Express Priority</option>
                  <option value="Same Day Hub Delivery">Same Day Hub Delivery</option>
                </select>
                {errors.deliveryType && <p className="mt-1 text-[11px] text-rose-400">{errors.deliveryType}</p>}
              </div>
            </div>
          </div>

          {/* Section 4: Routing & Specifications */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-sky-400 uppercase tracking-wider border-b border-slate-800 pb-2">
              4. Origin, Destination & Specs
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="originCity" className="block text-xs font-medium text-slate-300 mb-1">
                  Origin City / Hub <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  name="originCity"
                  id="originCity"
                  value={formData.originCity}
                  onChange={handleChange}
                  placeholder="e.g. Bangalore"
                  className={`w-full px-3.5 py-2.5 bg-slate-950 border ${
                    errors.originCity ? "border-rose-500 focus:ring-rose-500" : "border-slate-800 focus:ring-sky-500"
                  } rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2`}
                />
                {errors.originCity && <p className="mt-1 text-[11px] text-rose-400">{errors.originCity}</p>}
              </div>

              <div>
                <label htmlFor="destinationCity" className="block text-xs font-medium text-slate-300 mb-1">
                  Destination City / Hub <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  name="destinationCity"
                  id="destinationCity"
                  value={formData.destinationCity}
                  onChange={handleChange}
                  placeholder="e.g. Goa"
                  className={`w-full px-3.5 py-2.5 bg-slate-950 border ${
                    errors.destinationCity ? "border-rose-500 focus:ring-rose-500" : "border-slate-800 focus:ring-sky-500"
                  } rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2`}
                />
                {errors.destinationCity && <p className="mt-1 text-[11px] text-rose-400">{errors.destinationCity}</p>}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="pickupDate" className="block text-xs font-medium text-slate-300 mb-1">
                  Weight (kg) <span className="text-rose-400">* (&gt; 0)</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  name="weight"
                  value={formData.weight}
                  onChange={handleChange}
                  placeholder="e.g. 12.5"
                  className={`w-full px-3.5 py-2.5 bg-slate-950 border ${
                    errors.weight ? "border-rose-500 focus:ring-rose-500" : "border-slate-800 focus:ring-sky-500"
                  } rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2`}
                />
                {errors.weight && <p className="mt-1 text-[11px] text-rose-400">{errors.weight}</p>}
              </div>

              <div>
                <label htmlFor="estimatedCost" className="block text-xs font-medium text-slate-300 mb-1">
                  Estimated Cost (₹) <span className="text-slate-500">(Optional, &ge; 0)</span>
                </label>
                <input
                  type="number"
                  step="1"
                  min="0"
                  name="estimatedCost"
                  id="estimatedCost"
                  value={formData.estimatedCost}
                  onChange={handleChange}
                  placeholder="e.g. 1450"
                  className={`w-full px-3.5 py-2.5 bg-slate-950 border ${
                    errors.estimatedCost ? "border-rose-500 focus:ring-rose-500" : "border-slate-800 focus:ring-sky-500"
                  } rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2`}
                />
                {errors.estimatedCost && <p className="mt-1 text-[11px] text-rose-400">{errors.estimatedCost}</p>}
              </div>
            </div>
          </div>

          {/* Section 5: Schedule */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-sky-400 uppercase tracking-wider border-b border-slate-800 pb-2">
              5. Scheduling Dates
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="pickupDate" className="block text-xs font-medium text-slate-300 mb-1">
                  Pickup Date <span className="text-rose-400">*</span>
                </label>
                <input
                  type="date"
                  name="pickupDate"
                  id="pickupDate"
                  value={formData.pickupDate}
                  onChange={handleChange}
                  className={`w-full px-3.5 py-2.5 bg-slate-950 border ${
                    errors.pickupDate ? "border-rose-500 focus:ring-rose-500" : "border-slate-800 focus:ring-sky-500"
                  } rounded-xl text-xs text-white focus:outline-none focus:ring-2`}
                />
                {errors.pickupDate && <p className="mt-1 text-[11px] text-rose-400">{errors.pickupDate}</p>}
              </div>

              <div>
                <label htmlFor="expectedDeliveryDate" className="block text-xs font-medium text-slate-300 mb-1">
                  Expected Delivery Date <span className="text-rose-400">* (&ge; Pickup Date)</span>
                </label>
                <input
                  type="date"
                  name="expectedDeliveryDate"
                  id="expectedDeliveryDate"
                  value={formData.expectedDeliveryDate}
                  onChange={handleChange}
                  className={`w-full px-3.5 py-2.5 bg-slate-950 border ${
                    errors.expectedDeliveryDate ? "border-rose-500 focus:ring-rose-500" : "border-slate-800 focus:ring-sky-500"
                  } rounded-xl text-xs text-white focus:outline-none focus:ring-2`}
                />
                {errors.expectedDeliveryDate && <p className="mt-1 text-[11px] text-rose-400">{errors.expectedDeliveryDate}</p>}
              </div>
            </div>
          </div>

          {/* SUBMIT BUTTON */}
          <div className="pt-4 flex flex-col sm:flex-row items-center justify-end gap-3">
            {!isAuthenticated && !authLoading && (
              <p className="text-[11px] text-amber-300 sm:mr-auto">
                Sign in to enable shipment registration.
              </p>
            )}
            <button
              type="submit"
              disabled={isSubmitting || authLoading || !isAuthenticated}
              title={!isAuthenticated ? "Sign in to register a shipment" : undefined}
              className="w-full sm:w-auto px-8 py-3 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-semibold text-xs shadow-lg shadow-sky-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center space-x-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Creating Shipment in PostgreSQL...</span>
                </>
              ) : (
                <>
                  <PackageCheck className="w-4 h-4" />
                  <span>Register Shipment</span>
                </>
              )}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
