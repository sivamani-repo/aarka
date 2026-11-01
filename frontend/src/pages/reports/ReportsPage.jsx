import React, { useCallback, useEffect, useState } from 'react';
import {
  FileSpreadsheet,
  Download,
  BarChart3,
  TrendingUp,
  ShieldCheck,
  Package,
  CalendarDays,
  CheckCircle2,
  IndianRupee,
  ArrowUpRight,
  RefreshCw,
  FileDown,
  Boxes,
  HardHat,
  Wallet,
  Search,
  Clock3,
  Database,
  AlertCircle,
  X,
} from 'lucide-react';

import { reportsApi } from '../../services/api';
import StatCard from '../../components/common/StatCard';

const formatCurrency = (value) =>
  `₹${Number(value || 0).toLocaleString('en-IN', {
    maximumFractionDigits: 2,
  })}`;

const getCurrentDate = () => new Date().toISOString().split('T')[0];

const REPORTS = [
  {
    id: 'profitability',
    title: 'Project Profitability',
    subtitle: 'Cost & margin analysis',
    description:
      'Analyze sales order values, BOM component costs, technician labor expenses, and gross margins.',
    filename: `aarka_project_profitability_${getCurrentDate()}.csv`,
    badge: 'Financial Audit',
    icon: IndianRupee,
    accent: 'emerald',
    details: ['Revenue', 'Component costs', 'Labor costs', 'Gross margin'],
  },
  {
    id: 'inventory',
    title: 'Warehouse Inventory',
    subtitle: 'Stock & valuation',
    description:
      'Review stock levels across warehouses, unit costs, total inventory valuation, and low-stock alerts.',
    filename: `aarka_inventory_valuation_${getCurrentDate()}.csv`,
    badge: 'Warehouse',
    icon: Boxes,
    accent: 'blue',
    details: ['Stock levels', 'Unit costs', 'Stock valuation', 'Thresholds'],
  },
  {
    id: 'installations',
    title: 'Installation Operations',
    subtitle: 'Field operations & commissioning',
    description:
      'Track technician assignments, installation schedules, completion dates, checklist sign-offs, and customer handovers.',
    filename: `aarka_installations_${getCurrentDate()}.csv`,
    badge: 'Field Operations',
    icon: HardHat,
    accent: 'amber',
    details: ['Technicians', 'Schedules', 'Checklists', 'Handovers'],
  },
  {
    id: 'warranties',
    title: 'Warranty Registry',
    subtitle: 'Equipment & asset tracking',
    description:
      'Access equipment serial numbers, customer allocations, warranty periods, and current validity status.',
    filename: `aarka_warranty_registry_${getCurrentDate()}.csv`,
    badge: 'Asset Tracking',
    icon: ShieldCheck,
    accent: 'violet',
    details: ['Serial numbers', 'Customers', 'Validity', 'Expiry dates'],
  },
  {
    id: 'receivables',
    title: 'Accounts Receivable',
    subtitle: 'Collections & outstanding dues',
    description:
      'Monitor customer payment ledgers, milestone dues, recorded receipts, and outstanding balances.',
    filename: `aarka_outstanding_receivables_${getCurrentDate()}.csv`,
    badge: 'Treasury',
    icon: Wallet,
    accent: 'rose',
    details: ['Payment ledger', 'Milestones', 'Receipts', 'Outstanding dues'],
  },
];

const ACCENT_STYLES = {
  emerald: {
    icon: 'bg-emerald-50 text-emerald-700 ring-emerald-100',
    badge: 'bg-emerald-50 text-emerald-700 border-emerald-100',
    hover: 'group-hover:border-emerald-200',
  },
  blue: {
    icon: 'bg-blue-50 text-blue-700 ring-blue-100',
    badge: 'bg-blue-50 text-blue-700 border-blue-100',
    hover: 'group-hover:border-blue-200',
  },
  amber: {
    icon: 'bg-amber-50 text-amber-700 ring-amber-100',
    badge: 'bg-amber-50 text-amber-700 border-amber-100',
    hover: 'group-hover:border-amber-200',
  },
  violet: {
    icon: 'bg-violet-50 text-violet-700 ring-violet-100',
    badge: 'bg-violet-50 text-violet-700 border-violet-100',
    hover: 'group-hover:border-violet-200',
  },
  rose: {
    icon: 'bg-rose-50 text-rose-700 ring-rose-100',
    badge: 'bg-rose-50 text-rose-700 border-rose-100',
    hover: 'group-hover:border-rose-200',
  },
};

export default function ReportsPage() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [downloading, setDownloading] = useState(null);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');
  const [notification, setNotification] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchSummary = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError('');

      const res = await reportsApi.getDirectorSummary();

      setSummary(res.data);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to fetch executive summary:', err);
      setError('Unable to load the executive summary. Check your connection and try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  useEffect(() => {
    if (!notification) return;

    const timer = window.setTimeout(() => {
      setNotification(null);
    }, 3500);

    return () => window.clearTimeout(timer);
  }, [notification]);

  const handleDownloadCsv = async (reportType, filename) => {
    try {
      setDownloading(reportType);
      setNotification(null);

      let res;

      switch (reportType) {
        case 'profitability':
          res = await reportsApi.exportProfitability();
          break;

        case 'inventory':
          res = await reportsApi.exportInventory();
          break;

        case 'installations':
          res = await reportsApi.exportInstallations();
          break;

        case 'warranties':
          res = await reportsApi.exportWarranties();
          break;

        case 'receivables':
          res = await reportsApi.exportReceivables();
          break;

        default:
          throw new Error('Unsupported report type');
      }

      if (res?.data == null) {
        throw new Error('The server returned an empty response');
      }

      const blob =
        res.data instanceof Blob
          ? res.data
          : new Blob([res.data], {
            type: 'text/csv;charset=utf-8;',
          });

      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');

      anchor.href = url;
      anchor.download = filename;

      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();

      // Allow the browser to begin processing the download.
      window.setTimeout(() => {
        window.URL.revokeObjectURL(url);
      }, 1000);

      setNotification({
        type: 'success',
        message: `${filename} is ready for download.`,
      });
    } catch (err) {
      console.error('CSV export failed:', err);

      setNotification({
        type: 'error',
        message: 'Export failed. Please try again.',
      });
    } finally {
      setDownloading(null);
    }
  };

  const filteredReports = REPORTS.filter((report) => {
    const query = search.trim().toLowerCase();

    if (!query) return true;

    return [
      report.title,
      report.subtitle,
      report.description,
      report.badge,
      ...report.details,
    ]
      .join(' ')
      .toLowerCase()
      .includes(query);
  });

  const stats = [
    {
      title: 'Total Recognized Revenue',
      value: formatCurrency(summary?.total_revenue),
      icon: TrendingUp,
      subtitle: 'From confirmed sales orders',
      accent: 'emerald',
    },
    {
      title: 'Active Projects',
      value: (summary?.active_projects_count ?? 0).toLocaleString('en-IN'),
      icon: BarChart3,
      subtitle: 'Pipeline & installation',
      accent: 'blue',
    },
    {
      title: 'Completed Installations',
      value: (summary?.completed_installations_count ?? 0).toLocaleString(
        'en-IN'
      ),
      icon: CheckCircle2,
      subtitle: 'Customer handovers',
      accent: 'violet',
    },
    {
      title: 'Inventory Valuation',
      value: formatCurrency(summary?.inventory_value),
      icon: Package,
      subtitle: 'Across all warehouses',
      accent: 'amber',
    },
  ];

  return (
    <div className="enterprise-page enterprise-report-page space-y-7">
      {/* Notification */}
      {notification && (
        <div
          role="status"
          className={`fixed right-4 top-4 z-50 flex max-w-sm items-start gap-3 rounded-xl border bg-white p-4 shadow-xl ${notification.type === 'success'
            ? 'border-emerald-200'
            : 'border-rose-200'
            }`}
        >
          {notification.type === 'success' ? (
            <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" />
          ) : (
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-rose-600" />
          )}

          <p className="flex-1 text-sm font-medium text-stone-800">
            {notification.message}
          </p>

          <button
            onClick={() => setNotification(null)}
            className="text-stone-400 transition hover:text-stone-700"
            aria-label="Dismiss notification"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Page Header */}
      <section className="relative overflow-hidden rounded-2xl border border-stone-800 bg-stone-950 p-6 text-white shadow-sm sm:p-8">
        <div className="pointer-events-none absolute -right-16 -top-28 h-72 w-72 rounded-full border border-white/10" />
        <div className="pointer-events-none absolute -right-4 -top-16 h-56 w-56 rounded-full border border-white/10" />
        <div className="pointer-events-none absolute bottom-0 right-28 h-32 w-32 rounded-full bg-emerald-500/10 blur-3xl" />

        <div className="relative flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
          <div className="max-w-2xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1.5 text-xs font-medium text-emerald-300">
              <Database className="h-3.5 w-3.5" />
              Executive reporting
              <span className="h-1 w-1 rounded-full bg-emerald-400" />
              PostgreSQL
            </div>

            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
              Reports & Intelligence
            </h1>

            <p className="mt-3 max-w-xl text-sm leading-6 text-stone-400 sm:text-base">
              Monitor business performance, review operational metrics, and
              export structured reports from your solar installation platform.
            </p>

            <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-stone-400">
              <span className="inline-flex items-center gap-2">
                <span
                  className={`h-2 w-2 rounded-full ${error ? 'bg-rose-400' : 'bg-emerald-400'
                    }`}
                />
                {error ? 'Connection issue' : 'Reporting dashboard'}
              </span>

              <span className="inline-flex items-center gap-1.5">
                <CalendarDays className="h-3.5 w-3.5" />
                {new Date().toLocaleDateString('en-IN', {
                  day: '2-digit',
                  month: 'short',
                  year: 'numeric',
                })}
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={() => fetchSummary(true)}
            disabled={refreshing}
            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl border border-white/15 bg-white/5 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RefreshCw
              className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`}
            />
            {refreshing ? 'Refreshing...' : 'Refresh data'}
          </button>
        </div>
      </section>

      {/* Error State */}
      {error && (
        <div
          role="alert"
          className="flex flex-col gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 sm:flex-row sm:items-center sm:justify-between"
        >
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-rose-600" />
            <div>
              <p className="text-sm font-semibold text-rose-900">
                Executive summary unavailable
              </p>
              <p className="mt-1 text-sm text-rose-700">{error}</p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => fetchSummary(true)}
            className="shrink-0 rounded-lg border border-rose-200 bg-white px-3 py-2 text-sm font-semibold text-rose-700 transition hover:bg-rose-100"
          >
            Retry
          </button>
        </div>
      )}

      {/* Section Heading */}
      <section>
        <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-700">
              Business overview
            </p>
            <h2 className="mt-1 text-lg font-bold tracking-tight text-stone-900">
              Executive Summary
            </h2>
            <p className="mt-1 text-sm text-stone-500">
              Key performance indicators across your business.
            </p>
          </div>

          {lastUpdated && (
            <div className="inline-flex items-center gap-1.5 text-xs text-stone-500">
              <Clock3 className="h-3.5 w-3.5" />
              Updated at{' '}
              {lastUpdated.toLocaleTimeString('en-IN', {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </div>
          )}
        </div>

        <div className="enterprise-report-kpis grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {loading
            ? stats.map((stat) => (
              <div
                key={stat.title}
                className="animate-pulse rounded-2xl border border-stone-200 bg-white p-5"
              >
                <div className="flex items-center justify-between">
                  <div className="h-3 w-32 rounded bg-stone-200" />
                  <div className="h-10 w-10 rounded-xl bg-stone-100" />
                </div>
                <div className="mt-5 h-7 w-36 rounded bg-stone-200" />
                <div className="mt-3 h-3 w-40 rounded bg-stone-100" />
              </div>
            ))
            : stats.map((stat) => {
              const Icon = stat.icon;

              return (
                <div
                  key={stat.title}
                  className="group rounded-2xl border border-stone-200/80 bg-white p-5 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-stone-300 hover:shadow-md"
                >
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-sm font-medium leading-5 text-stone-500">
                      {stat.title}
                    </p>

                    <div
                      className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${ACCENT_STYLES[stat.accent].icon
                        }`}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                  </div>

                  <p className="mt-5 break-words text-2xl font-bold tracking-tight text-stone-950">
                    {stat.value}
                  </p>

                  <div className="mt-3 flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                    <p className="text-xs text-stone-500">{stat.subtitle}</p>
                  </div>
                </div>
              );
            })}
        </div>
      </section>

      {/* Report Catalog */}
      <section className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
        <div className="border-b border-stone-100 p-5 sm:p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-start gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-800">
                <FileSpreadsheet className="h-5 w-5" />
              </div>

              <div>
                <h2 className="text-lg font-bold tracking-tight text-stone-900">
                  Report Center
                </h2>
                <p className="mt-1 text-sm text-stone-500">
                  Export business data for operational reviews and financial
                  analysis.
                </p>
              </div>
            </div>

            <div className="relative w-full lg:max-w-xs">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />

              <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search reports..."
                aria-label="Search reports"
                className="w-full rounded-xl border border-stone-200 bg-stone-50 py-2.5 pl-9 pr-3 text-sm text-stone-800 outline-none transition placeholder:text-stone-400 focus:border-emerald-500 focus:bg-white focus:ring-4 focus:ring-emerald-500/10"
              />
            </div>
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-3 text-xs text-stone-500">
            <span className="inline-flex items-center gap-1.5 rounded-lg border border-stone-200 bg-stone-50 px-2.5 py-1.5">
              <FileDown className="h-3.5 w-3.5" />
              CSV format
            </span>

            <span className="inline-flex items-center gap-1.5 rounded-lg border border-stone-200 bg-stone-50 px-2.5 py-1.5">
              <ShieldCheck className="h-3.5 w-3.5" />
              Structured exports
            </span>

            <span className="ml-auto font-medium text-stone-600">
              {filteredReports.length} of {REPORTS.length} reports
            </span>
          </div>
        </div>

        {/* Report Cards */}
        <div className="grid grid-cols-1 gap-4 bg-stone-50/50 p-4 sm:p-5 lg:grid-cols-2">
          {filteredReports.map((report) => {
            const Icon = report.icon;
            const isDownloading = downloading === report.id;
            const styles = ACCENT_STYLES[report.accent];

            return (
              <article
                key={report.id}
                className={`group flex min-w-0 flex-col rounded-xl border border-stone-200 bg-white p-5 transition duration-200 hover:-translate-y-0.5 hover:shadow-md ${styles.hover}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div
                    className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ring-1 ${styles.icon}`}
                  >
                    <Icon className="h-5 w-5" />
                  </div>

                  <span
                    className={`rounded-lg border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider ${styles.badge}`}
                  >
                    {report.badge}
                  </span>
                </div>

                <div className="mt-4">
                  <h3 className="text-base font-bold tracking-tight text-stone-900">
                    {report.title}
                  </h3>

                  <p className="mt-1 text-xs font-medium text-stone-500">
                    {report.subtitle}
                  </p>

                  <p className="mt-3 min-h-[60px] text-sm leading-6 text-stone-600">
                    {report.description}
                  </p>
                </div>

                <div className="mt-4 flex flex-wrap gap-1.5">
                  {report.details.map((detail) => (
                    <span
                      key={detail}
                      className="rounded-md bg-stone-100 px-2 py-1 text-[10px] font-medium text-stone-600"
                    >
                      {detail}
                    </span>
                  ))}
                </div>

                <div className="mt-5 border-t border-stone-100 pt-4">
                  <div className="mb-3 flex items-center gap-2 text-[11px] text-stone-400">
                    <FileSpreadsheet className="h-3.5 w-3.5 shrink-0" />
                    <span className="min-w-0 break-all font-mono">
                      {report.filename}
                    </span>
                  </div>

                  <button
                    type="button"
                    disabled={Boolean(downloading)}
                    onClick={() =>
                      handleDownloadCsv(report.id, report.filename)
                    }
                    className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-stone-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-800 focus:outline-none focus:ring-4 focus:ring-emerald-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {isDownloading ? (
                      <>
                        <RefreshCw className="h-4 w-4 animate-spin" />
                        Generating export...
                      </>
                    ) : (
                      <>
                        <Download className="h-4 w-4" />
                        Download CSV
                        <ArrowUpRight className="ml-auto h-4 w-4 text-stone-400 transition group-hover:text-white" />
                      </>
                    )}
                  </button>
                </div>
              </article>
            );
          })}

          {filteredReports.length === 0 && (
            <div className="col-span-full flex flex-col items-center justify-center rounded-xl border border-dashed border-stone-300 bg-white px-5 py-14 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-stone-100 text-stone-500">
                <Search className="h-5 w-5" />
              </div>

              <h3 className="mt-4 text-sm font-semibold text-stone-900">
                No reports found
              </h3>

              <p className="mt-1 text-sm text-stone-500">
                Try a different search term.
              </p>

              <button
                type="button"
                onClick={() => setSearch('')}
                className="mt-4 text-sm font-semibold text-emerald-700 hover:text-emerald-800"
              >
                Clear search
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex flex-col gap-2 border-t border-stone-100 bg-white px-5 py-4 text-xs text-stone-500 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <span className="inline-flex items-center gap-2">
            <Database className="h-3.5 w-3.5" />
            AARKA Business Intelligence
          </span>

          <span>
            {lastUpdated
              ? `Last summary refresh: ${lastUpdated.toLocaleTimeString(
                'en-IN',
                {
                  hour: '2-digit',
                  minute: '2-digit',
                }
              )}`
              : 'Summary refresh pending'}
          </span>
        </div>
      </section>
    </div>
  );
}