
import React, { useCallback, useEffect, useState } from 'react';
import {
  Building2,
  Plus,
  Search,
  CheckCircle2,
  Clock3,
  AlertTriangle,
  FileCheck2,
  ShieldCheck,
  Landmark,
  RefreshCw,
  CalendarDays,
  IndianRupee,
  ArrowUpRight,
  Database,
  X,
  AlertCircle,
  Wallet,
  FileText,
  ChevronRight,
  Download,
} from 'lucide-react';

import { subsidiesApi } from '../../services/api';
import StatCard from '../../components/common/StatCard';
import StatusBadge from '../../components/common/StatusBadge';
import DataTable from '../../components/common/DataTable';
import Modal from '../../components/common/Modal';

const INITIAL_APPLY_FORM = {
  order_id: '',
  application_reference: '',
  discom_name: 'TSSPDCL',
  consumer_number: '',
  subsidy_scheme: 'PM_SURYA_GHAR_MUFT_BIJLI_YOJANA',
  eligible_amount: '78000',
};

const INITIAL_STATUS_FORM = {
  status: 'DOCS_VERIFIED',
  notes: '',
  inspection_date: '',
  sanctioned_amount: '78000',
  disbursement_reference: '',
};

const STATUS_OPTIONS = [
  { value: 'DRAFT', label: 'Draft' },
  { value: 'SUBMITTED', label: 'Submitted to Portal' },
  { value: 'DOCS_VERIFIED', label: 'Documents Verified' },
  { value: 'INSPECTION_SCHEDULED', label: 'Inspection Scheduled' },
  { value: 'INSPECTION_PASSED', label: 'Inspection Passed' },
  { value: 'APPROVED', label: 'Subsidy Approved' },
  { value: 'DISBURSED', label: 'Subsidy Disbursed' },
  { value: 'REJECTED', label: 'Rejected' },
];

const PENDING_STATUSES = [
  'SUBMITTED',
  'DOCS_VERIFIED',
  'INSPECTION_SCHEDULED',
];

const formatCurrency = (value) =>
  `₹${Number(value || 0).toLocaleString('en-IN', {
    maximumFractionDigits: 2,
  })}`;

const formatDate = (value) => {
  if (!value) return '—';

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
};

const getErrorMessage = (err, fallback) => {
  const detail = err.response?.data?.detail;

  if (typeof detail === 'string') return detail;

  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join(', ');
  }

  return fallback;
};

const inputClass =
  'w-full rounded-xl border border-stone-200 bg-white px-3.5 py-2.5 text-sm text-stone-800 outline-none transition placeholder:text-stone-400 focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10';

const labelClass =
  'mb-1.5 block text-xs font-semibold uppercase tracking-wider text-stone-600';

function SectionHeading({ eyebrow, title, description }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-700">
        {eyebrow}
      </p>

      <h2 className="mt-1 text-lg font-bold tracking-tight text-stone-900">
        {title}
      </h2>

      {description && (
        <p className="mt-1 text-sm text-stone-500">{description}</p>
      )}
    </div>
  );
}

function FeedbackBanner({ feedback, onDismiss }) {
  if (!feedback) return null;

  const isSuccess = feedback.type === 'success';

  return (
    <div
      role={isSuccess ? 'status' : 'alert'}
      className={`flex items-start gap-3 rounded-xl border p-4 ${isSuccess
        ? 'border-emerald-200 bg-emerald-50'
        : 'border-rose-200 bg-rose-50'
        }`}
    >
      {isSuccess ? (
        <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-700" />
      ) : (
        <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-rose-700" />
      )}

      <p
        className={`flex-1 text-sm font-medium ${isSuccess ? 'text-emerald-900' : 'text-rose-900'
          }`}
      >
        {feedback.msg}
      </p>

      <button
        type="button"
        onClick={onDismiss}
        aria-label="Dismiss notification"
        className="shrink-0 rounded-lg p-1 text-stone-500 transition hover:bg-black/5 hover:text-stone-900"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

function Field({ label, required, children, className = '' }) {
  return (
    <div className={className}>
      <label className={labelClass}>
        {label}
        {required && <span className="ml-1 text-rose-600">*</span>}
      </label>

      {children}
    </div>
  );
}

export default function SubsidiesPage() {
  const [subsidies, setSubsidies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const [showApplyModal, setShowApplyModal] = useState(false);
  const [showStatusModal, setShowStatusModal] = useState(false);

  const [selectedSubsidy, setSelectedSubsidy] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [fetchError, setFetchError] = useState('');

  const [applyForm, setApplyForm] = useState(INITIAL_APPLY_FORM);
  const [statusForm, setStatusForm] = useState(INITIAL_STATUS_FORM);

  const fetchSubsidies = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setFetchError('');

      const res = await subsidiesApi.getAll();

      setSubsidies(Array.isArray(res.data) ? res.data : []);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to fetch subsidy applications:', err);

      setFetchError(
        getErrorMessage(
          err,
          'Unable to load subsidy applications. Check your connection and try again.'
        )
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchSubsidies();
  }, [fetchSubsidies]);

  useEffect(() => {
    if (!feedback) return;

    const timer = window.setTimeout(() => {
      setFeedback(null);
    }, 5000);

    return () => window.clearTimeout(timer);
  }, [feedback]);

  const openApplyModal = () => {
    setFeedback(null);
    setApplyForm({ ...INITIAL_APPLY_FORM });
    setShowApplyModal(true);
  };

  const closeApplyModal = () => {
    if (submitting) return;
    setShowApplyModal(false);
  };

  const closeStatusModal = () => {
    if (submitting) return;
    setShowStatusModal(false);
    setSelectedSubsidy(null);
  };

  const handleApply = async (e) => {
    e.preventDefault();

    const orderId = Number(applyForm.order_id);
    const eligibleAmount = Number(applyForm.eligible_amount);

    if (!Number.isInteger(orderId) || orderId <= 0) {
      setFeedback({
        type: 'error',
        msg: 'Enter a valid positive sales order ID.',
      });
      return;
    }

    if (!Number.isFinite(eligibleAmount) || eligibleAmount < 0) {
      setFeedback({
        type: 'error',
        msg: 'Enter a valid non-negative subsidy amount.',
      });
      return;
    }

    try {
      setSubmitting(true);

      await subsidiesApi.create({
        ...applyForm,
        order_id: orderId,
        eligible_amount: eligibleAmount,
      });

      setShowApplyModal(false);
      setApplyForm({ ...INITIAL_APPLY_FORM });

      setFeedback({
        type: 'success',
        msg: 'Subsidy application registered successfully.',
      });

      await fetchSubsidies();
    } catch (err) {
      console.error('Failed to create subsidy application:', err);

      setFeedback({
        type: 'error',
        msg: getErrorMessage(err, 'Failed to register the application.'),
      });
    } finally {
      setSubmitting(false);
    }
  };

  const openStatusModal = (subsidy) => {
    setFeedback(null);
    setSelectedSubsidy(subsidy);

    setStatusForm({
      status: subsidy.status === 'DRAFT' ? 'SUBMITTED' : subsidy.status,
      notes: subsidy.discom_remarks || '',
      inspection_date: subsidy.inspection_scheduled_date
        ? String(subsidy.inspection_scheduled_date).slice(0, 10)
        : '',
      sanctioned_amount: String(
        subsidy.sanctioned_amount ?? subsidy.eligible_amount ?? ''
      ),
      disbursement_reference: subsidy.disbursement_reference || '',
    });

    setShowStatusModal(true);
  };

  const handleUpdateStatus = async (e) => {
    e.preventDefault();

    if (!selectedSubsidy) return;

    const requiresAmount = ['APPROVED', 'DISBURSED'].includes(
      statusForm.status
    );

    const sanctionedAmount =
      statusForm.sanctioned_amount === ''
        ? null
        : Number(statusForm.sanctioned_amount);

    if (
      requiresAmount &&
      (sanctionedAmount === null ||
        !Number.isFinite(sanctionedAmount) ||
        sanctionedAmount < 0)
    ) {
      setFeedback({
        type: 'error',
        msg: 'Enter a valid sanctioned amount.',
      });
      return;
    }

    try {
      setSubmitting(true);

      await subsidiesApi.updateStatus(selectedSubsidy.id, {
        status: statusForm.status,
        notes: statusForm.notes,
        inspection_date: statusForm.inspection_date || null,
        sanctioned_amount: sanctionedAmount,
        disbursement_reference:
          statusForm.disbursement_reference.trim() || null,
      });

      setShowStatusModal(false);
      setSelectedSubsidy(null);

      setFeedback({
        type: 'success',
        msg: `Application updated to ${STATUS_OPTIONS.find(
          (item) => item.value === statusForm.status
        )?.label || statusForm.status}.`,
      });

      await fetchSubsidies();
    } catch (err) {
      console.error('Failed to update subsidy status:', err);

      setFeedback({
        type: 'error',
        msg: getErrorMessage(err, 'Failed to update the application.'),
      });
    } finally {
      setSubmitting(false);
    }
  };

  const totalEligible = subsidies.reduce(
    (total, item) => total + Number(item.eligible_amount || 0),
    0
  );

  const totalDisbursed = subsidies.reduce(
    (total, item) => total + Number(item.disbursed_amount || 0),
    0
  );

  const pendingApprovals = subsidies.filter((item) =>
    PENDING_STATUSES.includes(item.status)
  ).length;

  const approvedCount = subsidies.filter((item) =>
    ['APPROVED', 'DISBURSED'].includes(item.status)
  ).length;

  const filtered = subsidies.filter((item) => {
    const query = search.trim().toLowerCase();

    const matchesSearch =
      !query ||
      [
        item.application_reference,
        item.consumer_number,
        item.discom_name,
        item.subsidy_scheme,
        item.order_id,
        item.status,
      ].some((value) => String(value ?? '').toLowerCase().includes(query));

    const matchesStatus =
      statusFilter === 'ALL' || item.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const columns = [
    {
      header: 'Application',
      accessor: 'application_reference',
      cell: (row) => (
        <div className="min-w-[145px]">
          <p className="font-mono text-sm font-bold text-emerald-800">
            {row.application_reference || `SUB-${row.id}`}
          </p>

          <p className="mt-1 text-xs text-stone-500">
            Created {formatDate(row.created_at)}
          </p>
        </div>
      ),
    },
    {
      header: 'Customer & Order',
      accessor: 'order_id',
      cell: (row) => (
        <div className="min-w-[140px]">
          <p className="text-sm font-semibold text-stone-900">
            Sales Order #{row.order_id}
          </p>

          <p className="mt-1 font-mono text-xs text-stone-500">
            {row.consumer_number || 'No consumer number'}
          </p>
        </div>
      ),
    },
    {
      header: 'DISCOM & Scheme',
      accessor: 'discom_name',
      cell: (row) => (
        <div className="min-w-[150px]">
          <p className="text-sm font-semibold text-stone-800">
            {row.discom_name || '—'}
          </p>

          <p className="mt-1 max-w-[220px] text-xs leading-5 text-stone-500">
            {row.subsidy_scheme === 'PM_SURYA_GHAR_MUFT_BIJLI_YOJANA'
              ? 'PM Surya Ghar Muft Bijli Yojana'
              : row.subsidy_scheme || '—'}
          </p>
        </div>
      ),
    },
    {
      header: 'Eligible Claim',
      accessor: 'eligible_amount',
      cell: (row) => (
        <span className="whitespace-nowrap text-sm font-bold text-stone-900">
          {formatCurrency(row.eligible_amount)}
        </span>
      ),
    },
    {
      header: 'Disbursed',
      accessor: 'disbursed_amount',
      cell: (row) => {
        const amount = Number(row.disbursed_amount || 0);

        return (
          <div>
            <p
              className={`whitespace-nowrap text-sm font-semibold ${amount > 0 ? 'text-emerald-700' : 'text-stone-400'
                }`}
            >
              {formatCurrency(amount)}
            </p>

            <p className="mt-1 text-[11px] text-stone-500">
              {amount > 0 ? 'Payment recorded' : 'Awaiting payment'}
            </p>
          </div>
        );
      },
    },
    {
      header: 'Lifecycle',
      accessor: 'status',
      cell: (row) => (
        <div className="min-w-[120px]">
          <StatusBadge status={row.status} />
        </div>
      ),
    },
    {
      header: 'Action',
      cell: (row) => (
        <button
          type="button"
          onClick={() => openStatusModal(row)}
          className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-lg border border-stone-200 bg-white px-3 py-2 text-xs font-semibold text-stone-700 transition hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-800 focus:outline-none focus:ring-4 focus:ring-emerald-500/10"
        >
          Manage
          <ChevronRight className="h-3.5 w-3.5" />
        </button>
      ),
    },
  ];

  const stats = [
    {
      title: 'Total Applications',
      value: subsidies.length.toLocaleString('en-IN'),
      icon: Landmark,
      subtitle: 'Registered subsidy files',
    },
    {
      title: 'Pending Approvals',
      value: pendingApprovals.toLocaleString('en-IN'),
      icon: Clock3,
      subtitle: 'Awaiting verification or inspection',
    },
    {
      title: 'Total Eligible Claims',
      value: formatCurrency(totalEligible),
      icon: FileCheck2,
      subtitle: 'Combined eligible claim amounts',
    },
    {
      title: 'Total Disbursed',
      value: formatCurrency(totalDisbursed),
      icon: Wallet,
      subtitle: 'Recorded customer disbursements',
    },
  ];

  return (
    <div className="min-h-screen space-y-7 bg-stone-50/70 p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <section className="relative overflow-hidden rounded-2xl border border-stone-800 bg-stone-950 p-6 text-white shadow-sm sm:p-8">
        <div className="pointer-events-none absolute -right-16 -top-24 h-64 w-64 rounded-full border border-white/10" />

        <div className="pointer-events-none absolute -right-5 -top-14 h-48 w-48 rounded-full border border-white/10" />

        <div className="pointer-events-none absolute bottom-0 right-24 h-32 w-32 rounded-full bg-emerald-500/10 blur-3xl" />

        <div className="relative flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
          <div className="max-w-2xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1.5 text-xs font-medium text-emerald-300">
              <ShieldCheck className="h-3.5 w-3.5" />
              Government liaison
              <span className="h-1 w-1 rounded-full bg-emerald-400" />
              Subsidy operations
            </div>

            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
              Subsidies & DISCOM Management
            </h1>

            <p className="mt-3 max-w-xl text-sm leading-6 text-stone-400 sm:text-base">
              Manage subsidy applications, monitor document verification,
              coordinate inspections, and track recorded disbursements across
              solar installation projects.
            </p>

            <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-stone-400">
              <span className="inline-flex items-center gap-2">
                <span
                  className={`h-2 w-2 rounded-full ${fetchError ? 'bg-rose-400' : 'bg-emerald-400'
                    }`}
                />
                {fetchError ? 'Connection issue' : 'Application register'}
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

          <div className="flex flex-col gap-2 sm:flex-row">
            <button
              type="button"
              onClick={() => fetchSubsidies(true)}
              disabled={refreshing}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/15 bg-white/5 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <RefreshCw
                className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`}
              />
              Refresh
            </button>

            <button
              type="button"
              onClick={openApplyModal}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-500 focus:outline-none focus:ring-4 focus:ring-emerald-400/20"
            >
              <Plus className="h-4 w-4" />
              New Application
            </button>
          </div>
        </div>
      </section>

      {/* Feedback */}
      <FeedbackBanner
        feedback={feedback}
        onDismiss={() => setFeedback(null)}
      />

      {/* Fetch Error */}
      {fetchError && (
        <div
          role="alert"
          className="flex flex-col gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 sm:flex-row sm:items-center sm:justify-between"
        >
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-rose-600" />

            <div>
              <p className="text-sm font-semibold text-rose-900">
                Unable to load subsidy records
              </p>

              <p className="mt-1 text-sm text-rose-700">{fetchError}</p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => fetchSubsidies(true)}
            className="shrink-0 rounded-lg border border-rose-200 bg-white px-3 py-2 text-sm font-semibold text-rose-700 transition hover:bg-rose-100"
          >
            Retry
          </button>
        </div>
      )}

      {/* KPI Section */}
      <section>
        <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <SectionHeading
            eyebrow="Business overview"
            title="Subsidy Performance"
            description="A consolidated view of application volume, claims, and recorded payments."
          />

          {lastUpdated && (
            <p className="text-xs text-stone-500">
              Updated{' '}
              {lastUpdated.toLocaleTimeString('en-IN', {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {loading
            ? stats.map((stat) => (
              <div
                key={stat.title}
                className="animate-pulse rounded-2xl border border-stone-200 bg-white p-5"
              >
                <div className="h-3 w-32 rounded bg-stone-200" />
                <div className="mt-5 h-7 w-36 rounded bg-stone-200" />
                <div className="mt-3 h-3 w-40 rounded bg-stone-100" />
              </div>
            ))
            : stats.map((stat, index) => {
              const icons = [
                Landmark,
                Clock3,
                IndianRupee,
                CheckCircle2,
              ];

              const Icon = icons[index];

              const iconStyles = [
                'bg-blue-50 text-blue-700',
                'bg-amber-50 text-amber-700',
                'bg-violet-50 text-violet-700',
                'bg-emerald-50 text-emerald-700',
              ];

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
                      className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${iconStyles[index]}`}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                  </div>

                  <p className="mt-5 break-words text-2xl font-bold tracking-tight text-stone-950">
                    {stat.value}
                  </p>

                  <p className="mt-3 text-xs leading-5 text-stone-500">
                    {stat.subtitle}
                  </p>
                </div>
              );
            })}
        </div>
      </section>

      {/* Application Register */}
      <section className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
        <div className="border-b border-stone-100 p-5 sm:p-6">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex items-start gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-800">
                <FileText className="h-5 w-5" />
              </div>

              <div>
                <h2 className="text-lg font-bold tracking-tight text-stone-900">
                  Application Register
                </h2>

                <p className="mt-1 text-sm text-stone-500">
                  Search records and manage subsidy lifecycle stages.
                </p>
              </div>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row">
              <div className="relative sm:w-72">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />

                <input
                  type="search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search application or consumer..."
                  aria-label="Search subsidy applications"
                  className={`${inputClass} pl-9`}
                />
              </div>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                aria-label="Filter by application status"
                className={`${inputClass} sm:w-52`}
              >
                <option value="ALL">All statuses</option>

                {STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-3 text-xs text-stone-500">
            <span className="inline-flex items-center gap-1.5 rounded-lg border border-stone-200 bg-stone-50 px-2.5 py-1.5">
              <Database className="h-3.5 w-3.5" />
              Application records
            </span>

            <span className="inline-flex items-center gap-1.5 rounded-lg border border-stone-200 bg-stone-50 px-2.5 py-1.5">
              <ShieldCheck className="h-3.5 w-3.5" />
              Lifecycle tracking
            </span>

            <span className="ml-auto font-medium text-stone-600">
              {filtered.length} of {subsidies.length} applications
            </span>
          </div>
        </div>

        <div className="min-w-0 overflow-x-auto">
          <DataTable
            columns={columns}
            data={filtered}
            loading={loading}
            emptyMessage={
              fetchError
                ? 'Subsidy records could not be loaded.'
                : 'No applications match your search or status filter.'
            }
          />
        </div>

        <div className="flex flex-col gap-2 border-t border-stone-100 bg-white px-5 py-4 text-xs text-stone-500 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <span className="inline-flex items-center gap-2">
            <Building2 className="h-3.5 w-3.5" />
            AARKA · Subsidy Operations
          </span>

          <span>
            {lastUpdated
              ? `Last refreshed: ${lastUpdated.toLocaleTimeString('en-IN', {
                hour: '2-digit',
                minute: '2-digit',
              })}`
              : 'Waiting for application records'}
          </span>
        </div>
      </section>

      {/* New Application Modal */}
      <Modal
        isOpen={showApplyModal}
        onClose={closeApplyModal}
        title="Register Subsidy Application"
      >
        <form onSubmit={handleApply} className="space-y-5">
          <div className="rounded-xl border border-emerald-100 bg-emerald-50/70 p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white text-emerald-800 shadow-sm">
                <Landmark className="h-4 w-4" />
              </div>

              <div>
                <p className="text-sm font-semibold text-emerald-950">
                  PM Surya Ghar Muft Bijli Yojana
                </p>

                <p className="mt-1 text-xs leading-5 text-emerald-800">
                  Register the application reference and electricity consumer
                  details associated with the sales order.
                </p>
              </div>
            </div>
          </div>

          <Field label="Sales Order ID" required>
            <input
              type="number"
              min="1"
              step="1"
              required
              placeholder="Enter sales order ID"
              value={applyForm.order_id}
              onChange={(e) =>
                setApplyForm({
                  ...applyForm,
                  order_id: e.target.value,
                })
              }
              className={inputClass}
            />
          </Field>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Portal Application Reference" required>
              <input
                type="text"
                required
                maxLength={100}
                placeholder="PMSGY-2026-98124"
                value={applyForm.application_reference}
                onChange={(e) =>
                  setApplyForm({
                    ...applyForm,
                    application_reference: e.target.value,
                  })
                }
                className={`${inputClass} font-mono`}
              />
            </Field>

            <Field label="Consumer / USC Number" required>
              <input
                type="text"
                required
                maxLength={100}
                placeholder="Consumer number"
                value={applyForm.consumer_number}
                onChange={(e) =>
                  setApplyForm({
                    ...applyForm,
                    consumer_number: e.target.value,
                  })
                }
                className={`${inputClass} font-mono`}
              />
            </Field>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="DISCOM Name" required>
              <input
                type="text"
                required
                maxLength={100}
                placeholder="e.g. TSSPDCL"
                value={applyForm.discom_name}
                onChange={(e) =>
                  setApplyForm({
                    ...applyForm,
                    discom_name: e.target.value,
                  })
                }
                className={inputClass}
              />
            </Field>

            <Field label="Eligible Subsidy Amount (₹)" required>
              <input
                type="number"
                min="0"
                step="0.01"
                required
                value={applyForm.eligible_amount}
                onChange={(e) =>
                  setApplyForm({
                    ...applyForm,
                    eligible_amount: e.target.value,
                  })
                }
                className={inputClass}
              />
            </Field>
          </div>

          <div className="flex flex-col-reverse gap-2 border-t border-stone-100 pt-4 sm:flex-row sm:justify-end">
            <button
              type="button"
              onClick={closeApplyModal}
              disabled={submitting}
              className="rounded-xl border border-stone-200 px-4 py-2.5 text-sm font-semibold text-stone-700 transition hover:bg-stone-50 disabled:opacity-50"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting && (
                <RefreshCw className="h-4 w-4 animate-spin" />
              )}

              {submitting ? 'Registering...' : 'Register Application'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Update Lifecycle Modal */}
      <Modal
        isOpen={showStatusModal}
        onClose={closeStatusModal}
        title="Manage Subsidy Application"
      >
        {selectedSubsidy && (
          <form onSubmit={handleUpdateStatus} className="space-y-5">
            <div className="rounded-xl border border-stone-200 bg-stone-50 p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-stone-500">
                    Application reference
                  </p>

                  <p className="mt-1 break-all font-mono text-sm font-bold text-emerald-800">
                    {selectedSubsidy.application_reference ||
                      `SUB-${selectedSubsidy.id}`}
                  </p>

                  <p className="mt-2 text-xs text-stone-600">
                    Sales Order #{selectedSubsidy.order_id}
                  </p>
                </div>

                <StatusBadge status={selectedSubsidy.status} />
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 border-t border-stone-200 pt-4">
                <div>
                  <p className="text-xs text-stone-500">Eligible amount</p>
                  <p className="mt-1 text-sm font-bold text-stone-900">
                    {formatCurrency(selectedSubsidy.eligible_amount)}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-stone-500">Disbursed amount</p>
                  <p className="mt-1 text-sm font-bold text-emerald-700">
                    {formatCurrency(selectedSubsidy.disbursed_amount)}
                  </p>
                </div>
              </div>
            </div>

            <Field label="Application Lifecycle Stage" required>
              <select
                required
                value={statusForm.status}
                onChange={(e) =>
                  setStatusForm({
                    ...statusForm,
                    status: e.target.value,
                  })
                }
                className={inputClass}
              >
                {STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </Field>

            {[
              'INSPECTION_SCHEDULED',
              'INSPECTION_PASSED',
            ].includes(statusForm.status) && (
                <Field label="DISCOM Inspection Date">
                  <input
                    type="date"
                    value={statusForm.inspection_date}
                    onChange={(e) =>
                      setStatusForm({
                        ...statusForm,
                        inspection_date: e.target.value,
                      })
                    }
                    className={inputClass}
                  />
                </Field>
              )}

            {['APPROVED', 'DISBURSED'].includes(statusForm.status) && (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Sanctioned Amount (₹)" required>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    required
                    value={statusForm.sanctioned_amount}
                    onChange={(e) =>
                      setStatusForm({
                        ...statusForm,
                        sanctioned_amount: e.target.value,
                      })
                    }
                    className={inputClass}
                  />
                </Field>

                <Field label="DBT Reference / UTR">
                  <input
                    type="text"
                    maxLength={150}
                    placeholder="Enter payment reference"
                    value={statusForm.disbursement_reference}
                    onChange={(e) =>
                      setStatusForm({
                        ...statusForm,
                        disbursement_reference: e.target.value,
                      })
                    }
                    className={`${inputClass} font-mono`}
                  />
                </Field>
              </div>
            )}

            {statusForm.status === 'DISBURSED' && (
              <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" />

                <p className="text-xs leading-5 text-amber-900">
                  Verify the actual payment and UTR against the authoritative
                  payment record before marking the application as disbursed.
                </p>
              </div>
            )}

            <Field label="Official Remarks / Notes">
              <textarea
                rows={4}
                maxLength={2000}
                placeholder="Record inspection findings, document verification, or official remarks..."
                value={statusForm.notes}
                onChange={(e) =>
                  setStatusForm({
                    ...statusForm,
                    notes: e.target.value,
                  })
                }
                className={`${inputClass} resize-y`}
              />

              <p className="mt-1 text-right text-xs text-stone-400">
                {statusForm.notes.length}/2000
              </p>
            </Field>

            <div className="flex flex-col-reverse gap-2 border-t border-stone-100 pt-4 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={closeStatusModal}
                disabled={submitting}
                className="rounded-xl border border-stone-200 px-4 py-2.5 text-sm font-semibold text-stone-700 transition hover:bg-stone-50 disabled:opacity-50"
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {submitting && (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                )}

                {submitting ? 'Saving...' : 'Save Lifecycle Stage'}
                {!submitting && <ArrowUpRight className="h-4 w-4" />}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}
