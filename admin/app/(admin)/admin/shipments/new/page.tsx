"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowLeft, PackagePlus, CheckCircle, UserCheck, Loader2 } from "lucide-react";
import { adminApiClient } from "@/lib/api-client";

export default function NewShipmentPage() {
  const [customerEmail, setCustomerEmail] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [shipperName, setShipperName] = useState("");
  const [recipientName, setRecipientName] = useState("");
  const [packageName, setPackageName] = useState("");
  // No pre-filled values: the previous defaults ("10" kg, "40x30x30 cm",
  // "EXPRESS", "1500") were silently persisted as real freight data whenever an
  // operator left a field untouched.
  const [weightKg, setWeightKg] = useState("");
  const [dimensions, setDimensions] = useState("");
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [deliveryType, setDeliveryType] = useState("");
  const [cost, setCost] = useState("");
  const [pickupDate, setPickupDate] = useState("");
  const [expectedDeliveryDate, setExpectedDeliveryDate] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [createdTrackingId, setCreatedTrackingId] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    /**
     * Reject incomplete input instead of substituting invented values
     * (`customerName || "Enterprise Client"`, `weightKg || 10.0`,
     * `cost_inr || 1500.0`), which used to write fabricated freight records.
     */
    const weightValue = Number.parseFloat(weightKg);
    const costValue = Number.parseFloat(cost);
    const missing: string[] = [];
    if (!customerEmail.trim()) missing.push("customer email");
    if (!customerName.trim()) missing.push("customer name");
    if (!shipperName.trim()) missing.push("shipper name");
    if (!recipientName.trim()) missing.push("recipient name");
    if (!packageName.trim()) missing.push("cargo description");
    if (!deliveryType.trim()) missing.push("delivery type");
    if (!origin.trim()) missing.push("origin");
    if (!destination.trim()) missing.push("destination");
    if (!pickupDate) missing.push("pickup date");
    if (!expectedDeliveryDate) missing.push("expected delivery date");

    if (missing.length > 0) {
      setErrorMsg(`Please complete the following required fields: ${missing.join(", ")}.`);
      return;
    }

    if (!Number.isFinite(weightValue) || weightValue <= 0) {
      setErrorMsg("Weight (kg) must be a number greater than 0.");
      return;
    }

    if (!Number.isFinite(costValue) || costValue < 0) {
      setErrorMsg("Estimated cost (₹) must be a number of 0 or greater.");
      return;
    }

    if (expectedDeliveryDate < pickupDate) {
      setErrorMsg("Expected delivery date cannot be before the pickup date.");
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = {
        customer_email: customerEmail.trim(),
        customer_name: customerName.trim(),
        shipper_name: shipperName.trim(),
        recipient_name: recipientName.trim(),
        package_name: packageName.trim(),
        weight_kg: weightValue,
        dimensions: dimensions.trim() || undefined,
        origin: origin.trim(),
        destination: destination.trim(),
        delivery_type: deliveryType,
        cost_inr: costValue,
        pickup_date: pickupDate,
        expected_delivery_date: expectedDeliveryDate
      };

      const res = await adminApiClient.post<any>("/admin/shipments", payload);
      if (res && res.success && res.shipment) {
        setCreatedTrackingId(res.shipment.tracking_id);
      } else {
        throw new Error(res.message || "Failed to create shipment");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to submit shipment to backend.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Link href="/admin/shipments" className="inline-flex items-center text-xs text-indigo-400 hover:text-indigo-300 space-x-1.5">
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Shipments</span>
      </Link>

      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <PackagePlus className="w-6 h-6 text-indigo-400" />
          <span>Register New Shipment (On Behalf of Customer)</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Create operational consignment in PostgreSQL database with backend-validated tracking ID
        </p>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          {errorMsg}
        </div>
      )}

      {createdTrackingId ? (
        <div className="p-8 rounded-2xl bg-slate-900 border border-emerald-500/40 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto">
            <CheckCircle className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-white">Shipment Registered in Database</h2>
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 inline-block">
            <span className="text-xs text-slate-500 block uppercase tracking-wider mb-1">Backend Generated Tracking ID</span>
            <span className="font-mono text-2xl text-emerald-400 font-bold tracking-wider">{createdTrackingId}</span>
          </div>
          <div>
            <Link
              href="/admin/shipments"
              className="inline-block mt-4 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
            >
              Return to Shipments List
            </Link>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="shipCustomerEmail" className="block text-xs font-medium text-slate-300 mb-1">Customer Email</label>
              <input
                id="shipCustomerEmail"
                type="email"
                required
                value={customerEmail}
                onChange={(e) => setCustomerEmail(e.target.value)}
                placeholder="customer@domain.com"
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
              />
            </div>

            <div>
              <label htmlFor="shipCustomerName" className="block text-xs font-medium text-slate-300 mb-1">Customer Name / Entity</label>
              <input
                id="shipCustomerName"
                type="text"
                required
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                placeholder="Rahul Verma / Reliance Retail"
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
              />
            </div>

            <div>
              <label htmlFor="shipShipperName" className="block text-xs font-medium text-slate-300 mb-1">Shipper Name</label>
              <input
                id="shipShipperName"
                type="text"
                required
                value={shipperName}
                onChange={(e) => setShipperName(e.target.value)}
                placeholder="Sender Name / Warehouse"
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
              />
            </div>

            <div>
              <label htmlFor="shipRecipientName" className="block text-xs font-medium text-slate-300 mb-1">Recipient Name</label>
              <input
                id="shipRecipientName"
                type="text"
                required
                value={recipientName}
                onChange={(e) => setRecipientName(e.target.value)}
                placeholder="Recipient Name / Distribution Hub"
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
              />
            </div>

            <div>
              <label htmlFor="shipPackageName" className="block text-xs font-medium text-slate-300 mb-1">Cargo Description / Package</label>
              <input
                id="shipPackageName"
                type="text"
                required
                value={packageName}
                onChange={(e) => setPackageName(e.target.value)}
                placeholder="e.g. Industrial Electronics Box"
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
              />
            </div>

            <div>
              <label htmlFor="shipDeliveryType" className="block text-xs font-medium text-slate-300 mb-1">Delivery Type</label>
              <select
                id="shipDeliveryType"
                required
                value={deliveryType}
                onChange={(e) => setDeliveryType(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
              >
                <option value="" disabled>Select delivery type...</option>
                <option value="STANDARD">Standard Road Freight</option>
                <option value="EXPRESS">Express Priority</option>
                <option value="SAME_DAY">Same Day Hub Delivery</option>
              </select>
            </div>

            <div>
              <label htmlFor="shipOrigin" className="block text-xs font-medium text-slate-300 mb-1">Origin City / Hub</label>
              <input
                id="shipOrigin"
                type="text"
                required
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
                placeholder="e.g. Mumbai Hub"
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
              />
            </div>

            <div>
              <label htmlFor="shipDestination" className="block text-xs font-medium text-slate-300 mb-1">Destination City / Hub</label>
              <input
                id="shipDestination"
                type="text"
                required
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                placeholder="e.g. Delhi NCR"
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
              />
            </div>

            <div>
              <label htmlFor="shipWeightKg" className="block text-xs font-medium text-slate-300 mb-1">Weight (kg)</label>
              <input
                id="shipWeightKg"
                type="number"
                min="0.1"
                step="0.1"
                required
                value={weightKg}
                onChange={(e) => setWeightKg(e.target.value)}
                placeholder="e.g. 12.5"
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
              />
            </div>

            <div>
              <label htmlFor="shipCost" className="block text-xs font-medium text-slate-300 mb-1">Estimated Cost (₹)</label>
              <input
                id="shipCost"
                type="number"
                min="0"
                step="1"
                required
                value={cost}
                onChange={(e) => setCost(e.target.value)}
                placeholder="e.g. 1450"
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
              />
            </div>

            <div>
              <label htmlFor="shipDimensions" className="block text-xs font-medium text-slate-300 mb-1">Dimensions (optional)</label>
              <input
                id="shipDimensions"
                type="text"
                value={dimensions}
                onChange={(e) => setDimensions(e.target.value)}
                placeholder="e.g. 40x30x30 cm"
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
              />
            </div>

            <div>
              <label htmlFor="shipPickupDate" className="block text-xs font-medium text-slate-300 mb-1">Pickup Date</label>
              <input
                id="shipPickupDate"
                type="date"
                required
                value={pickupDate}
                onChange={(e) => setPickupDate(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
              />
            </div>

            <div>
              <label htmlFor="shipExpectedDate" className="block text-xs font-medium text-slate-300 mb-1">Expected Delivery Date</label>
              <input
                id="shipExpectedDate"
                type="date"
                required
                value={expectedDeliveryDate}
                onChange={(e) => setExpectedDeliveryDate(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-400 hover:to-violet-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-indigo-500/20 disabled:opacity-50 transition-all flex items-center justify-center space-x-2"
          >
            {isSubmitting && <Loader2 className="w-4 h-4 animate-spin text-white" />}
            <span>{isSubmitting ? "Persisting to Database..." : "Create Shipment & Generate Tracking ID"}</span>
          </button>
        </form>
      )}
    </div>
  );
}
