"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Users, UserPlus, Loader2, RefreshCw, CheckCircle, ShieldCheck } from "lucide-react";
import { adminApiClient } from "@/lib/api-client";
import { useEscapeToClose } from "@/lib/use-modal";

export default function AdminDriversPage() {
  const [drivers, setDrivers] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Add Driver Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form Fields
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [gender, setGender] = useState("Male");
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("Mumbai");
  const [state, setState] = useState("Maharashtra");
  const [pin, setPin] = useState("");
  const [licenseNumber, setLicenseNumber] = useState("");
  const [maskedAadhaar, setMaskedAadhaar] = useState("");
  const [employmentType, setEmploymentType] = useState("FULL_TIME");
  const [experienceYears, setExperienceYears] = useState("3");
  const [baseLocation, setBaseLocation] = useState("Mumbai Hub");
  const [serviceArea, setServiceArea] = useState("Western Zone");

  const closeModal = useCallback(() => setIsModalOpen(false), []);
  useEscapeToClose(isModalOpen, closeModal);

  const fetchDrivers = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await adminApiClient.get<any>("/admin/drivers");
      if (res && res.success) {
        setDrivers(res.drivers || []);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to fetch drivers from backend.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDrivers();
  }, []);

  const handleAddDriver = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const payload = {
        full_name: fullName,
        phone,
        email: email || undefined,
        date_of_birth: dateOfBirth || undefined,
        gender,
        address,
        city,
        state,
        pin,
        license_number: licenseNumber,
        masked_aadhaar: maskedAadhaar,
        employment_type: employmentType,
        experience_years: parseInt(experienceYears) || 3,
        base_location: baseLocation,
        service_area: serviceArea
      };

      const res = await adminApiClient.post<any>("/admin/drivers", payload);
      if (res && res.success && res.driver) {
        setSuccessMsg(`Driver '${res.driver.full_name}' (${res.driver.driver_id}) created successfully in database.`);
        setIsModalOpen(false);
        // Reset form
        setFullName("");
        setPhone("");
        setEmail("");
        setLicenseNumber("");
        setMaskedAadhaar("");
        await fetchDrivers();
      } else {
        throw new Error(res.message || "Failed to create driver");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to save driver to database.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Users className="w-6 h-6 text-indigo-400" />
            <span>Driver Fleet Management</span>
            {isLoading && <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Administered drivers, KYC verification, driving license tracking, and assignment state persisted in PostgreSQL.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchDrivers}
            disabled={isLoading}
            className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
            title="Refresh List"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin text-indigo-400" : ""}`} />
          </button>

          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-400 hover:to-violet-500 text-white font-medium text-xs shadow-md shadow-indigo-500/20 transition-all"
          >
            <UserPlus className="w-4 h-4" />
            <span>+ Add New Driver</span>
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          {errorMsg}
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-semibold">
          âœ“ {successMsg}
        </div>
      )}

      {/* Driver List Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        {isLoading ? (
          <div className="py-16 text-center text-slate-500">
            <Loader2 className="w-8 h-8 mx-auto mb-3 animate-spin text-indigo-400" />
            <p className="text-xs">Fetching drivers from database...</p>
          </div>
        ) : drivers.length === 0 ? (
          <div className="p-12 text-center">
            <Users className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <h4 className="text-sm font-semibold text-white">No drivers registered</h4>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Click &apos;+ Add New Driver&apos; to register your first fleet driver in the database.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                <tr>
                  <th scope="col" className="p-3 font-semibold">Driver ID</th>
                  <th scope="col" className="p-3 font-semibold">Full Name</th>
                  <th scope="col" className="p-3 font-semibold">Contact</th>
                  <th scope="col" className="p-3 font-semibold">License No.</th>
                  <th scope="col" className="p-3 font-semibold">Base Location</th>
                  <th scope="col" className="p-3 font-semibold">KYC / License</th>
                  <th scope="col" className="p-3 font-semibold">Status</th>
                  <th scope="col" className="p-3 font-semibold">Data Mode</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {drivers.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-3 font-mono text-indigo-400 font-bold">{d.driver_id}</td>
                    <td className="p-3 font-medium text-white">{d.full_name}</td>
                    <td className="p-3 text-slate-300">
                      <div>{d.phone}</div>
                      <div className="text-[10px] text-slate-500">{d.email || "No email"}</div>
                    </td>
                    <td className="p-3 font-mono text-slate-400">{d.license_number || "N/A"}</td>
                    <td className="p-3 text-slate-300">{d.base_location}</td>
                    <td className="p-3 space-x-1">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        KYC: {d.kyc_status}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
                        {d.license_status}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-semibold border ${
                        d.status === "AVAILABLE"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : "bg-indigo-500/10 text-indigo-400 border-indigo-500/20"
                      }`}>
                        {d.status}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                        d.is_demo
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                          : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                      }`}>
                        {d.is_demo ? "DEMO DATA" : "LIVE"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Driver Modal */}
      {isModalOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="add-driver-title"
        >
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <h3 id="add-driver-title" className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <UserPlus className="w-5 h-5 text-indigo-400" />
              <span>Add New Driver (PostgreSQL Persistence)</span>
            </h3>

            <form onSubmit={handleAddDriver} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Full Name</label>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Ramesh Singh"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Phone Number</label>
                  <input
                    type="text"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+91 98765 43210"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="ramesh@driver.travelogix.internal"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">License Number</label>
                  <input
                    type="text"
                    required
                    value={licenseNumber}
                    onChange={(e) => setLicenseNumber(e.target.value)}
                    placeholder="MH0420200054321"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Masked Aadhaar</label>
                  <input
                    type="text"
                    value={maskedAadhaar}
                    onChange={(e) => setMaskedAadhaar(e.target.value)}
                    placeholder="XXXX-XXXX-1234"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Date of Birth</label>
                  <input
                    type="date"
                    value={dateOfBirth}
                    onChange={(e) => setDateOfBirth(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Base Location / Hub</label>
                  <input
                    type="text"
                    value={baseLocation}
                    onChange={(e) => setBaseLocation(e.target.value)}
                    placeholder="e.g. Mumbai Hub"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Service Area</label>
                  <input
                    type="text"
                    value={serviceArea}
                    onChange={(e) => setServiceArea(e.target.value)}
                    placeholder="e.g. Western Corridor"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-400 hover:to-violet-500 text-white text-xs font-semibold disabled:opacity-50 flex items-center space-x-2"
                >
                  {isSubmitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Save Driver to Database</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
