"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Truck, Plus, Loader2, RefreshCw, CheckCircle } from "lucide-react";
import { adminApiClient } from "@/lib/api-client";
import { useEscapeToClose } from "@/lib/use-modal";

export default function AdminVehiclesPage() {
  const [vehicles, setVehicles] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Add Vehicle Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form Fields â€” intentionally empty: the previous defaults ("Heavy Container",
  // "Tata Prima 3530.K", "15 Tons", "Diesel") persisted invented fleet data
  // whenever an operator saved the form without touching those fields.
  const [registrationNumber, setRegistrationNumber] = useState("");
  const [vehicleType, setVehicleType] = useState("");
  const [model, setModel] = useState("");
  const [capacity, setCapacity] = useState("");
  const [fuelType, setFuelType] = useState("");

  const closeModal = useCallback(() => setIsModalOpen(false), []);
  useEscapeToClose(isModalOpen, closeModal);

  const fetchVehicles = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await adminApiClient.get<any>("/admin/vehicles");
      if (res && res.success) {
        setVehicles(res.vehicles || []);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to fetch vehicles from backend.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchVehicles();
  }, []);

  const handleAddVehicle = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    // Reject incomplete input instead of persisting fabricated vehicle data.
    if (!registrationNumber.trim() || !vehicleType.trim() || !model.trim() || !capacity.trim() || !fuelType.trim()) {
      setErrorMsg("Registration number, vehicle type, model, capacity and fuel type are all required.");
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = {
        registration_number: registrationNumber.trim(),
        vehicle_type: vehicleType,
        model: model.trim(),
        capacity: capacity.trim(),
        fuel_type: fuelType
      };

      const res = await adminApiClient.post<any>("/admin/vehicles", payload);
      if (res && res.success && res.vehicle) {
        setSuccessMsg(`Vehicle '${res.vehicle.registration_number}' added successfully to database.`);
        setIsModalOpen(false);
        setRegistrationNumber("");
        setVehicleType("");
        setModel("");
        setCapacity("");
        setFuelType("");
        await fetchVehicles();
      } else {
        throw new Error(res.message || "Failed to add vehicle");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to save vehicle to database.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Truck className="w-6 h-6 text-indigo-400" />
            <span>Fleet Vehicles Management</span>
            {isLoading && <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Vehicle registrations, RC, insurance, PUC, and capacity tracking persisted in PostgreSQL.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchVehicles}
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
            <Plus className="w-4 h-4" />
            <span>+ Add New Vehicle</span>
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

      {/* Vehicle List Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        {isLoading ? (
          <div className="py-16 text-center text-slate-500">
            <Loader2 className="w-8 h-8 mx-auto mb-3 animate-spin text-indigo-400" />
            <p className="text-xs">Fetching fleet vehicles from database...</p>
          </div>
        ) : vehicles.length === 0 ? (
          <div className="p-12 text-center">
            <Truck className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <h4 className="text-sm font-semibold text-white">No vehicles registered</h4>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Click &apos;+ Add New Vehicle&apos; to register transport fleet vehicles in the database.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                <tr>
                  <th scope="col" className="p-3 font-semibold">Vehicle ID</th>
                  <th scope="col" className="p-3 font-semibold">Registration Number</th>
                  <th scope="col" className="p-3 font-semibold">Vehicle Type & Model</th>
                  <th scope="col" className="p-3 font-semibold">Capacity</th>
                  <th scope="col" className="p-3 font-semibold">Fuel Type</th>
                  <th scope="col" className="p-3 font-semibold">Compliance / Documents</th>
                  <th scope="col" className="p-3 font-semibold">Status</th>
                  <th scope="col" className="p-3 font-semibold">Data Mode</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {vehicles.map((v) => (
                  <tr key={v.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-3 font-mono text-indigo-400 font-bold">{v.vehicle_id}</td>
                    <td className="p-3 font-mono font-bold text-white">{v.registration_number}</td>
                    <td className="p-3 text-slate-300">
                      <div className="font-medium text-white">{v.vehicle_type}</div>
                      <div className="text-[10px] text-slate-500">{v.model}</div>
                    </td>
                    <td className="p-3 text-slate-300">{v.capacity}</td>
                    <td className="p-3 text-slate-400 font-medium">{v.fuel_type}</td>
                    <td className="p-3 space-x-1">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        RC: {v.rc_status}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
                        INS: {v.insurance_status}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-semibold border ${
                        v.status === "ACTIVE"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : "bg-indigo-500/10 text-indigo-400 border-indigo-500/20"
                      }`}>
                        {v.status}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                        v.is_demo
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                          : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                      }`}>
                        {v.is_demo ? "DEMO DATA" : "LIVE"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Vehicle Modal */}
      {isModalOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="add-vehicle-title"
        >
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4">
            <h3 id="add-vehicle-title" className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <Truck className="w-5 h-5 text-indigo-400" />
              <span>Add New Vehicle (PostgreSQL Persistence)</span>
            </h3>

            <form onSubmit={handleAddVehicle} className="space-y-4">
              <div>
                <label htmlFor="vehicleRegNumber" className="block text-xs font-medium text-slate-300 mb-1">Registration Number</label>
                <input
                  id="vehicleRegNumber"
                  type="text"
                  required
                  value={registrationNumber}
                  onChange={(e) => setRegistrationNumber(e.target.value)}
                  placeholder="e.g. MH-04-CD-9999"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white uppercase font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="vehicleType" className="block text-xs font-medium text-slate-300 mb-1">Vehicle Type</label>
                  <select
                    id="vehicleType"
                    required
                    value={vehicleType}
                    onChange={(e) => setVehicleType(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                  >
                    <option value="" disabled>Select vehicle type...</option>
                    <option value="Heavy Container">Heavy Container</option>
                    <option value="Medium Truck">Medium Truck</option>
                    <option value="Flatbed Trailer">Flatbed Trailer</option>
                    <option value="Delivery Van">Delivery Van</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="vehicleModel" className="block text-xs font-medium text-slate-300 mb-1">Model Name</label>
                  <input
                    id="vehicleModel"
                    type="text"
                    required
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    placeholder="e.g. Tata Prima 3530.K"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="vehicleCapacity" className="block text-xs font-medium text-slate-300 mb-1">Payload Capacity</label>
                  <input
                    id="vehicleCapacity"
                    type="text"
                    required
                    value={capacity}
                    onChange={(e) => setCapacity(e.target.value)}
                    placeholder="e.g. 15 Tons"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>

                <div>
                  <label htmlFor="vehicleFuelType" className="block text-xs font-medium text-slate-300 mb-1">Fuel Type</label>
                  <select
                    id="vehicleFuelType"
                    required
                    value={fuelType}
                    onChange={(e) => setFuelType(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                  >
                    <option value="" disabled>Select fuel type...</option>
                    <option value="Diesel">Diesel</option>
                    <option value="EV / Electric">EV / Electric</option>
                    <option value="CNG">CNG</option>
                  </select>
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
                  <span>Save Vehicle to DB</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
