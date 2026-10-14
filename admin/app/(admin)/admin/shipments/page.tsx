"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { Package, PlusCircle, Search, Filter, Loader2, RefreshCw, UserCheck, ShieldCheck } from "lucide-react";
import { adminApiClient } from "@/lib/api-client";
import { useEscapeToClose } from "@/lib/use-modal";

export default function AdminShipmentsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [shipments, setShipments] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Assignment Modal state
  const [selectedShipment, setSelectedShipment] = useState<any | null>(null);
  const [eligibleDrivers, setEligibleDrivers] = useState<any[]>([]);
  const [selectedDriverId, setSelectedDriverId] = useState("");
  const [assignmentNotes, setAssignmentNotes] = useState("");
  const [isAssigning, setIsAssigning] = useState(false);

  // Status Change state
  const [statusUpdatingId, setStatusUpdatingId] = useState<string | null>(null);

  const fetchShipments = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await adminApiClient.get<any>("/admin/shipments");
      if (res && res.success) {
        setShipments(res.shipments || []);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load shipments from backend.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchShipments();
  }, []);

  const openAssignModal = async (shipment: any) => {
    setSelectedShipment(shipment);
    setSelectedDriverId("");
    setAssignmentNotes("");
    try {
      const res = await adminApiClient.get<any>("/admin/drivers/eligible");
      if (res && res.success) {
        setEligibleDrivers(res.drivers || []);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to fetch eligible drivers.");
    }
  };

  const closeAssignModal = useCallback(() => {
    setSelectedShipment(null);
    setSelectedDriverId("");
    setAssignmentNotes("");
  }, []);

  useEscapeToClose(Boolean(selectedShipment), closeAssignModal);

  const handleAssignDriver = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedShipment || !selectedDriverId) return;
    setIsAssigning(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await adminApiClient.post<any>("/admin/assignments", {
        shipment_id: selectedShipment.id,
        driver_id: selectedDriverId,
        notes: assignmentNotes
      });

      if (res && res.success) {
        setSuccessMsg(`Assigned driver successfully to ${selectedShipment.tracking_id}`);
        setSelectedShipment(null);
        await fetchShipments();
      } else {
        throw new Error(res.message || "Assignment failed");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to assign driver.");
    } finally {
      setIsAssigning(false);
    }
  };

  const handleStatusChange = async (shipmentId: string, trackingId: string, newStatus: string) => {
    setStatusUpdatingId(shipmentId);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await adminApiClient.patch<any>(`/admin/shipments/${trackingId}`, {
        status: newStatus
      });

      if (res && res.success) {
        setSuccessMsg(`Updated status of ${trackingId} to ${newStatus}`);
        await fetchShipments();
      } else {
        throw new Error(res.message || "Status update failed");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update status.");
    } finally {
      setStatusUpdatingId(null);
    }
  };

  const filteredShipments = shipments.filter((s) => {
    const matchesSearch =
      s.tracking_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.shipper_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.origin?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.destination?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === "ALL" || s.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <span>Shipments Management</span>
            {isLoading && <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />}
          </h1>
          <p className="text-xs text-slate-400 mt-1">Review, dispatch, and track consignments persisted in PostgreSQL</p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchShipments}
            disabled={isLoading}
            className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
            title="Refresh List"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin text-indigo-400" : ""}`} />
          </button>
          <Link
            href="/admin/shipments/new"
            className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-400 hover:to-violet-500 text-white font-medium text-xs shadow-md shadow-indigo-500/20 transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>+ Register New Shipment</span>
          </Link>
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

      {/* Filter and Search Bar */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by Tracking ID, Customer, Shipper, Route..."
            className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-slate-500" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="REGISTERED">Registered</option>
            <option value="PICKUP_SCHEDULED">Pickup Scheduled</option>
            <option value="PICKED_UP">Picked Up</option>
            <option value="IN_TRANSIT">In Transit</option>
            <option value="ARRIVED_AT_HUB">Arrived at Hub</option>
            <option value="OUT_FOR_DELIVERY">Out for Delivery</option>
            <option value="DELIVERED">Delivered</option>
            <option value="DELAYED">Delayed</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Table / List */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        {isLoading ? (
          <div className="py-16 text-center text-slate-500">
            <Loader2 className="w-8 h-8 mx-auto mb-3 animate-spin text-indigo-400" />
            <p className="text-xs">Fetching shipments from PostgreSQL database...</p>
          </div>
        ) : filteredShipments.length === 0 ? (
          <div className="py-16 text-center text-slate-500">
            <Package className="w-10 h-10 mx-auto mb-3 opacity-30 text-indigo-400" />
            <h4 className="text-sm font-semibold text-slate-300">No shipments found</h4>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              No orders currently match your criteria.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs whitespace-nowrap">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                <tr>
                  <th scope="col" className="p-3 font-semibold">Tracking ID</th>
                  <th scope="col" className="p-3 font-semibold">Customer</th>
                  <th scope="col" className="p-3 font-semibold">Shipper</th>
                  <th scope="col" className="p-3 font-semibold">Recipient</th>
                  <th scope="col" className="p-3 font-semibold">Cargo</th>
                  <th scope="col" className="p-3 font-semibold">Delivery Type</th>
                  <th scope="col" className="p-3 font-semibold">Origin</th>
                  <th scope="col" className="p-3 font-semibold">Destination</th>
                  <th scope="col" className="p-3 font-semibold">Weight</th>
                  <th scope="col" className="p-3 font-semibold">Cost</th>
                  <th scope="col" className="p-3 font-semibold">Pickup Date</th>
                  <th scope="col" className="p-3 font-semibold">Expected Date</th>
                  <th scope="col" className="p-3 font-semibold">Status</th>
                  <th scope="col" className="p-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredShipments.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-3 font-mono text-indigo-400 font-bold">{s.tracking_id}</td>
                    <td className="p-3 text-slate-200">
                      <div className="font-medium">{s.customer_name}</div>
                      <div className="text-[10px] text-slate-500">{s.customer_email}</div>
                    </td>
                    <td className="p-3 text-slate-300">{s.shipper_name || "N/A"}</td>
                    <td className="p-3 text-slate-300">{s.recipient_name || "N/A"}</td>
                    <td className="p-3 text-slate-300">{s.package_name || "Standard Cargo"}</td>
                    <td className="p-3 text-slate-400 font-medium">{s.delivery_type}</td>
                    <td className="p-3 text-slate-300">{s.origin}</td>
                    <td className="p-3 text-slate-300">{s.destination}</td>
                    <td className="p-3 text-slate-300 font-mono">{s.weight_kg} kg</td>
                    <td className="p-3 text-emerald-400 font-mono font-semibold">â‚¹{s.cost_inr}</td>
                    <td className="p-3 text-slate-400">{s.pickup_date || "N/A"}</td>
                    <td className="p-3 text-slate-400">{s.expected_delivery_date || "N/A"}</td>
                    <td className="p-3">
                      <select
                        value={s.status}
                        disabled={statusUpdatingId === s.id}
                        onChange={(e) => handleStatusChange(s.id, s.tracking_id, e.target.value)}
                        className="px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-white font-medium focus:ring-1 focus:ring-indigo-500"
                      >
                        <option value="REGISTERED">REGISTERED</option>
                        <option value="PICKUP_SCHEDULED">PICKUP_SCHEDULED</option>
                        <option value="PICKED_UP">PICKED_UP</option>
                        <option value="IN_TRANSIT">IN_TRANSIT</option>
                        <option value="ARRIVED_AT_HUB">ARRIVED_AT_HUB</option>
                        <option value="OUT_FOR_DELIVERY">OUT_FOR_DELIVERY</option>
                        <option value="DELIVERED">DELIVERED</option>
                        <option value="DELAYED">DELAYED</option>
                        <option value="CANCELLED">CANCELLED</option>
                      </select>
                    </td>
                    <td className="p-3 text-right space-x-2">
                      <button
                        onClick={() => openAssignModal(s)}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 hover:bg-indigo-500/20 transition-colors text-[11px]"
                      >
                        <UserCheck className="w-3.5 h-3.5" />
                        <span>Assign Driver</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Driver Assignment Modal */}
      {selectedShipment && (
        <div
          className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="assign-driver-title"
        >
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4">
            <h3 id="assign-driver-title" className="text-base font-bold text-white flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-indigo-400" />
              <span>Assign Driver to {selectedShipment.tracking_id}</span>
            </h3>

            <form onSubmit={handleAssignDriver} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Eligible Driver</label>
                <select
                  required
                  value={selectedDriverId}
                  onChange={(e) => setSelectedDriverId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                >
                  <option value="">Select an available active driver...</option>
                  {eligibleDrivers.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.full_name} ({d.driver_id}) - {d.status}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Assignment Notes (Optional)</label>
                <textarea
                  value={assignmentNotes}
                  onChange={(e) => setAssignmentNotes(e.target.value)}
                  placeholder="Specific dispatch instructions..."
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white h-20"
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={closeAssignModal}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!selectedDriverId || isAssigning}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold disabled:opacity-50 flex items-center space-x-2"
                >
                  {isAssigning && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Assign & Update DB</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
