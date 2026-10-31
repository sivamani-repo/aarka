import React, { useState, useEffect } from 'react';
import { 
  FileSpreadsheet, Download, BarChart2, TrendingUp, ShieldCheck, 
  Package, Calendar, CheckCircle2, DollarSign, ArrowUpRight 
} from 'lucide-react';
import { reportsApi } from '../../services/api';
import StatCard from '../../components/common/StatCard';

export default function ReportsPage() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(null);

  useEffect(() => {
    fetchSummary();
  }, []);

  const fetchSummary = async () => {
    try {
      setLoading(true);
      const res = await reportsApi.getDirectorSummary();
      setSummary(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadCsv = async (reportType, filename) => {
    try {
      setDownloading(reportType);
      let res;
      if (reportType === 'profitability') res = await reportsApi.exportProfitability();
      else if (reportType === 'inventory') res = await reportsApi.exportInventory();
      else if (reportType === 'installations') res = await reportsApi.exportInstallations();
      else if (reportType === 'warranties') res = await reportsApi.exportWarranties();
      else if (reportType === 'receivables') res = await reportsApi.exportReceivables();

      // Trigger browser download
      const blob = new Blob([res.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Download failed:', err);
      alert('Failed to download CSV export');
    } finally {
      setDownloading(null);
    }
  };

  const exportCards = [
    {
      id: 'profitability',
      title: 'Project Profitability & Cost Ledger (Rule #15)',
      description: 'Breakdown of sales order value, BOM component costs, technician labor costs, and net gross margin percentage.',
      filename: `aarka_project_profitability_${new Date().toISOString().split('T')[0]}.csv`,
      badge: 'Financial Audit'
    },
    {
      id: 'inventory',
      title: 'Warehouse Inventory & Stock Valuation',
      description: 'Complete stock levels across warehouses, unit costs, total inventory valuation, and minimum threshold alert status.',
      filename: `aarka_inventory_valuation_${new Date().toISOString().split('T')[0]}.csv`,
      badge: 'Warehouse'
    },
    {
      id: 'installations',
      title: 'Installation Operations & Commissioning Report',
      description: 'Technician assignments, scheduled dates, completion dates, 9-point checklist sign-offs, and customer acceptance.',
      filename: `aarka_installations_${new Date().toISOString().split('T')[0]}.csv`,
      badge: 'Field Ops'
    },
    {
      id: 'warranties',
      title: 'Active Warranties & Serial Numbers Registry',
      description: 'Customer allocations, Tier-1 manufacturer equipment serial numbers, start & end dates, and current validity status.',
      filename: `aarka_warranty_registry_${new Date().toISOString().split('T')[0]}.csv`,
      badge: 'Asset Tracking'
    },
    {
      id: 'receivables',
      title: 'Outstanding Accounts Receivable & Collections',
      description: 'Customer payment ledger, milestone dues, recorded receipts, and pending balance collections per sales order.',
      filename: `aarka_outstanding_receivables_${new Date().toISOString().split('T')[0]}.csv`,
      badge: 'Treasury'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-stone-900 tracking-tight">Executive Intelligence & CSV Exports</h1>
        <p className="text-sm text-stone-600 mt-1">
          One-click audit-grade CSV data extractions computed live from PostgreSQL database records.
        </p>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Recognized Revenue"
          value={`₹${(summary?.total_revenue || 0).toLocaleString('en-IN')}`}
          icon={TrendingUp}
          subtitle="From confirmed sales orders"
        />
        <StatCard
          title="Active Projects"
          value={summary?.active_projects_count || 0}
          icon={BarChart2}
          subtitle="In pipeline & installation"
        />
        <StatCard
          title="Completed Commissions"
          value={summary?.completed_installations_count || 0}
          icon={CheckCircle2}
          subtitle="Handed over to customers"
        />
        <StatCard
          title="Total Inventory Value"
          value={`₹${(summary?.inventory_value || 0).toLocaleString('en-IN')}`}
          icon={Package}
          subtitle="Stock across all warehouses"
        />
      </div>

      {/* Export List Cards */}
      <div className="bg-white rounded-xl border border-stone-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-stone-200">
          <div>
            <h2 className="text-lg font-bold text-stone-900">Live Database CSV Exports</h2>
            <p className="text-xs text-stone-500">Download formatted CSV reports directly for board reviews and CA tax filing.</p>
          </div>
          <FileSpreadsheet className="w-5 h-5 text-emerald-800" />
        </div>

        <div className="divide-y divide-stone-100">
          {exportCards.map((card) => (
            <div key={card.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2 py-0.5 rounded font-medium bg-emerald-50 text-emerald-800 border border-emerald-200">
                    {card.badge}
                  </span>
                  <h3 className="font-semibold text-stone-900 text-sm">{card.title}</h3>
                </div>
                <p className="text-xs text-stone-600 max-w-2xl">{card.description}</p>
                <div className="text-[11px] font-mono text-stone-400">File: {card.filename}</div>
              </div>

              <button
                disabled={downloading === card.id}
                onClick={() => handleDownloadCsv(card.id, card.filename)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-stone-900 hover:bg-stone-800 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors whitespace-nowrap disabled:opacity-50"
              >
                <Download className="w-4 h-4 text-emerald-400" />
                {downloading === card.id ? 'Exporting...' : 'Download CSV'}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
