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
  Calculator,
  Sliders,
  Check,
  Upload,
  ExternalLink,
  Layers,
  Sparkles,
  Info,
  HelpCircle,
  Eye,
  ArrowRight,
  CheckCircle,
  XCircle,
  FileSpreadsheet,
  Users,
  Compass
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  CartesianGrid
} from 'recharts';

import { subsidiesApi, customersApi } from '../../services/api';
import StatCard from '../../components/common/StatCard';
import StatusBadge from '../../components/common/StatusBadge';
import DataTable from '../../components/common/DataTable';
import Modal from '../../components/common/Modal';

const TABS = [
  { id: 'overview', label: 'Overview & Analytics', icon: Landmark },
  { id: 'schemes', label: 'Government Schemes', icon: Layers },
  { id: 'eligibility', label: 'Check Eligibility', icon: ShieldCheck },
  { id: 'calculator', label: 'Subsidy Calculator', icon: Calculator },
  { id: 'applications', label: 'Application Register', icon: FileText },
  { id: 'tracker', label: 'Track Application', icon: Compass },
];

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899', '#6366f1'];

const formatCurrency = (val) =>
  `₹${Number(val || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

const formatDate = (val) => {
  if (!val) return '—';
  const d = new Date(val);
  if (Number.isNaN(d.getTime())) return val;
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
};

const inputClass =
  'w-full rounded-xl border border-stone-200 bg-white px-3.5 py-2.5 text-sm text-stone-800 outline-none transition placeholder:text-stone-400 focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10';

const labelClass = 'block text-xs font-semibold text-stone-600 mb-1.5 uppercase tracking-wider';

export default function SubsidiesPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Dashboard Data
  const [metrics, setMetrics] = useState(null);
  const [schemes, setSchemes] = useState([]);
  const [subsidies, setSubsidies] = useState([]);
  const [customers, setCustomers] = useState([]);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [schemeCategoryFilter, setSchemeCategoryFilter] = useState('ALL');

  // Modals & Drawers
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [selectedScheme, setSelectedScheme] = useState(null);
  const [schemeChecklist, setSchemeChecklist] = useState(null);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [appDocuments, setAppDocuments] = useState([]);
  const [appHistory, setAppHistory] = useState([]);
  const [showDocUploadModal, setShowDocUploadModal] = useState(false);
  const [showOfficialUpdateModal, setShowOfficialUpdateModal] = useState(false);

  // New Application Form State
  const [applyForm, setApplyForm] = useState({
    customer_id: '',
    category: 'RESIDENTIAL',
    state: 'Telangana',
    discom_name: 'TSSPDCL',
    consumer_number: '',
    capacity_kw: '3.0',
    subsidy_amount: '78000',
    remarks: '',
  });

  // Eligibility Wizard State
  const [wizardStep, setWizardStep] = useState(1);
  const [eligibilityForm, setEligibilityForm] = useState({
    applicant_name: '',
    applicant_phone: '',
    applicant_email: '',
    customer_category: 'RESIDENTIAL',
    state: 'Telangana',
    district: 'Hyderabad',
    discom_name: 'TSSPDCL',
    consumer_number: '',
    tariff_category: 'LT-1 Residential',
    sanctioned_load_kw: '3.0',
    monthly_consumption_units: '250',
    proposed_capacity: '3.0',
    roof_type: 'RCC Flat Concrete',
    available_roof_area_sqft: '300',
    has_roof_rights: true,
    is_grid_connected: true,
    prior_subsidy_claimed: false,
    scheme_code: 'PM_SURYA_GHAR_RES',
  });
  const [assessmentResult, setAssessmentResult] = useState(null);
  const [assessing, setAssessing] = useState(false);

  // Subsidy Calculator State
  const [calcInputs, setCalcInputs] = useState({
    capacity_kw: 3.0,
    category: 'RESIDENTIAL',
    state: 'Telangana',
  });
  const [calcOutput, setCalcOutput] = useState(null);
  const [calculating, setCalculating] = useState(false);

  // Tracker State
  const [trackerSearch, setTrackerSearch] = useState('');
  const [trackedApplication, setTrackedApplication] = useState(null);
  const [trackingLoading, setTrackingLoading] = useState(false);
  const [trackingError, setTrackingError] = useState('');

  // Document Upload State
  const [uploadDocType, setUploadDocType] = useState('ELECTRICITY_BILL');
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  // Official Status Update State
  const [officialStatusForm, setOfficialStatusForm] = useState({
    official_status: 'SUBMITTED',
    portal_application_ref: '',
    evidence_reference: '',
    remarks: '',
    approved_amount: '78000',
    disbursed_amount: '78000',
    disbursement_reference: '',
  });

  // Initial Fetch
  const loadData = useCallback(async () => {
    try {
      setRefreshing(true);
      setErrorMsg('');
      const [mRes, sRes, subRes, custRes] = await Promise.all([
        subsidiesApi.getDashboardMetrics(),
        subsidiesApi.getSchemes(),
        subsidiesApi.getSubsidies(),
        customersApi.getAll ? customersApi.getAll() : Promise.resolve({ data: [] }),
      ]);
      setMetrics(mRes.data);
      setSchemes(sRes.data || []);
      setSubsidies(subRes.data || []);
      setCustomers(custRes.data || []);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to load subsidy metrics:', err);
      setErrorMsg('Could not fetch subsidy governance data. Please check connection.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Recalculate whenever calculator inputs change
  useEffect(() => {
    const fetchCalc = async () => {
      setCalculating(true);
      try {
        const res = await subsidiesApi.calculate({
          capacity_kw: calcInputs.capacity_kw,
          category: calcInputs.category,
          state: calcInputs.state,
        });
        setCalcOutput(res.data);
      } catch (err) {
        console.error('Calculation error:', err);
      } finally {
        setCalculating(false);
      }
    };
    fetchCalc();
  }, [calcInputs]);

  // Handle Assessment Submit
  const handleCheckEligibility = async (e) => {
    e.preventDefault();
    setAssessing(true);
    setErrorMsg('');
    try {
      const res = await subsidiesApi.checkEligibility({
        customer_name: eligibilityForm.applicant_name,
        category: eligibilityForm.customer_category,
        state: eligibilityForm.state,
        discom_name: eligibilityForm.discom_name,
        consumer_number: eligibilityForm.consumer_number,
        capacity_kw: parseFloat(eligibilityForm.proposed_capacity) || 3.0,
        is_grid_connected: eligibilityForm.is_grid_connected,
        prior_subsidy_claimed: eligibilityForm.prior_subsidy_claimed,
      });
      setAssessmentResult(res.data);
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Eligibility check failed. Please check inputs.');
    } finally {
      setAssessing(false);
    }
  };

  // Open Scheme Details Modal
  const openSchemeModal = async (sch) => {
    setSelectedScheme(sch);
    try {
      const res = await subsidiesApi.getSchemeDocuments(sch.code);
      setSchemeChecklist(res.data);
    } catch (err) {
      setSchemeChecklist(null);
    }
  };

  // Open Application Detail Drawer
  const openAppDrawer = async (app) => {
    setSelectedApplication(app);
    try {
      const [dRes, hRes] = await Promise.all([
        subsidiesApi.getDocuments(app.id),
        subsidiesApi.getHistory(app.id),
      ]);
      setAppDocuments(dRes.data || []);
      setAppHistory(hRes.data || []);
    } catch (err) {
      console.error('Error fetching details:', err);
    }
  };

  // Handle Create Application
  const handleCreateApplication = async (e) => {
    e.preventDefault();
    try {
      await subsidiesApi.createSubsidy({
        customer_id: parseInt(applyForm.customer_id, 10),
        category: applyForm.category,
        state: applyForm.state,
        discom_name: applyForm.discom_name,
        consumer_number: applyForm.consumer_number,
        capacity_kw: parseFloat(applyForm.capacity_kw),
        subsidy_amount: parseFloat(applyForm.subsidy_amount),
        remarks: applyForm.remarks,
      });
      setShowApplyModal(false);
      setSuccessMsg('Government subsidy application registered successfully.');
      loadData();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to create application.');
    }
  };

  // Handle Document Upload
  const handleUploadDocument = async (e) => {
    e.preventDefault();
    if (!uploadFile || !selectedApplication) return;
    setUploading(true);
    const fd = new FormData();
    fd.append('file', uploadFile);
    fd.append('doc_type', uploadDocType);
    try {
      await subsidiesApi.uploadSubsidyDoc(selectedApplication.id, fd);
      setShowDocUploadModal(false);
      setUploadFile(null);
      setSuccessMsg('Document securely uploaded. Level 1 automated validation completed.');
      // Refresh application drawer
      openAppDrawer(selectedApplication);
      loadData();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Document upload failed.');
    } finally {
      setUploading(false);
    }
  };

  // Handle Level 2 Employee Review
  const handleReviewDocument = async (docId, decision, remarks = '') => {
    try {
      await subsidiesApi.reviewDocument(docId, { decision, remarks });
      setSuccessMsg(`Document marked ${decision} by AARKA review team.`);
      if (selectedApplication) {
        openAppDrawer(selectedApplication);
      }
      loadData();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Document review action failed.');
    }
  };

  // Handle Level 3 Official Status Update
  const handleUpdateOfficialStatus = async (e) => {
    e.preventDefault();
    if (!selectedApplication) return;
    try {
      await subsidiesApi.updateOfficialStatus(selectedApplication.id, {
        official_status: officialStatusForm.official_status,
        portal_application_ref: officialStatusForm.portal_application_ref,
        evidence_reference: officialStatusForm.evidence_reference,
        remarks: officialStatusForm.remarks,
        approved_amount: parseFloat(officialStatusForm.approved_amount) || 0,
        disbursed_amount: parseFloat(officialStatusForm.disbursed_amount) || 0,
        disbursement_reference: officialStatusForm.disbursement_reference,
      });
      setShowOfficialUpdateModal(false);
      setSuccessMsg('Official government status synchronized successfully.');
      if (selectedApplication) {
        openAppDrawer(selectedApplication);
      }
      loadData();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to update official status.');
    }
  };

  // Handle Customer Tracker Search
  const handleTrackSearch = async (e) => {
    e.preventDefault();
    if (!trackerSearch.trim()) return;
    setTrackingLoading(true);
    setTrackingError('');
    setTrackedApplication(null);
    try {
      const res = await subsidiesApi.trackApplication(trackerSearch.trim());
      setTrackedApplication(res.data);
    } catch (err) {
      setTrackingError(err.response?.data?.detail || 'No application record found for this reference.');
    } finally {
      setTrackingLoading(false);
    }
  };

  // Filtered applications
  const filteredApps = subsidies.filter((app) => {
    if (statusFilter !== 'ALL') {
      const st = app.official_status || app.approval_status;
      if (st !== statusFilter) return false;
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      const name = (app.customer_name || '').toLowerCase();
      const num = (app.application_number || '').toLowerCase();
      const ref = (app.portal_application_ref || '').toLowerCase();
      const usc = (app.consumer_number || '').toLowerCase();
      return name.includes(q) || num.includes(q) || ref.includes(q) || usc.includes(q);
    }
    return true;
  });

  const columns = [
    {
      header: 'Application Ref',
      accessor: (row) => (
        <div>
          <span className="font-semibold text-stone-900 block">{row.application_number}</span>
          <span className="text-xs text-stone-400 font-mono">
            {row.portal_application_ref || 'Pending Portal Ref'}
          </span>
        </div>
      ),
    },
    {
      header: 'Customer & Meter',
      accessor: (row) => (
        <div>
          <span className="font-medium text-stone-800 block">{row.customer_name || '—'}</span>
          <span className="text-xs text-stone-500">
            {row.discom_name} · USC: {row.consumer_number || 'N/A'}
          </span>
        </div>
      ),
    },
    {
      header: 'System',
      accessor: (row) => (
        <span className="text-xs font-medium text-stone-700 bg-stone-100 px-2 py-1 rounded-md">
          {row.capacity_kw} kW ({row.category})
        </span>
      ),
    },
    {
      header: 'Internal Verification',
      accessor: (row) => (
        <StatusBadge status={row.internal_status || row.verification_status || 'DRAFT'} />
      ),
    },
    {
      header: 'Official Govt Status',
      accessor: (row) => (
        <StatusBadge status={row.official_status || row.approval_status || 'NOT_SUBMITTED'} />
      ),
    },
    {
      header: 'Assistance (DBT)',
      accessor: (row) => (
        <div>
          <span className="font-semibold text-emerald-800 block">
            {formatCurrency(row.disbursed_amount > 0 ? row.disbursed_amount : (row.approved_amount > 0 ? row.approved_amount : row.subsidy_amount))}
          </span>
          <span className="text-[10px] uppercase font-semibold text-stone-400">
            {row.disbursed_amount > 0 ? 'Disbursed' : (row.approved_amount > 0 ? 'Sanctioned' : 'Estimated')}
          </span>
        </div>
      ),
    },
    {
      header: 'Action',
      accessor: (row) => (
        <button
          onClick={() => openAppDrawer(row)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-stone-200 bg-white text-xs font-semibold text-stone-700 hover:bg-stone-50 hover:border-stone-300 shadow-sm transition"
        >
          <Eye className="h-3.5 w-3.5 text-emerald-600" />
          Review & Track
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-emerald-900 via-stone-900 to-emerald-950 p-6 text-white shadow-xl sm:p-8">
        <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-2xl">
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase tracking-widest">
              <Landmark className="h-4 w-4" />
              <span>Government Schemes & DBT Assistance</span>
            </div>
            <h1 className="mt-2 text-2xl font-bold tracking-tight text-white sm:text-3xl">
              Government Subsidy & Governance Desk
            </h1>
            <p className="mt-2 text-sm text-stone-300 leading-relaxed">
              Explore national and state solar incentives, perform instant eligibility checks under PM Surya Ghar & PM-KUSUM guidelines, manage document compliance, and track official DBT disbursement directly from DISCOM and National Portals.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={loadData}
              disabled={refreshing}
              className="inline-flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2.5 text-xs font-semibold text-white backdrop-blur-md transition hover:bg-white/20"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={() => setShowApplyModal(true)}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-500 px-4 py-2.5 text-xs font-semibold text-white shadow-lg shadow-emerald-500/25 transition hover:bg-emerald-600"
            >
              <Plus className="h-4 w-4" />
              Register Subsidy Application
            </button>
          </div>
        </div>

        {/* Decorative Grid */}
        <div className="absolute -right-10 -bottom-10 h-64 w-64 rounded-full bg-emerald-500/10 blur-3xl" />
      </div>

      {/* Notifications / Alerts */}
      {errorMsg && (
        <div className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          <AlertCircle className="h-5 w-5 shrink-0 text-red-600" />
          <span>{errorMsg}</span>
          <button onClick={() => setErrorMsg('')} className="ml-auto text-red-600 hover:text-red-800">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
      {successMsg && (
        <div className="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
          <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600" />
          <span>{successMsg}</span>
          <button onClick={() => setSuccessMsg('')} className="ml-auto text-emerald-600 hover:text-emerald-800">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex overflow-x-auto border-b border-stone-200 pb-1 gap-2">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 whitespace-nowrap rounded-xl px-4 py-2.5 text-xs font-semibold transition ${
                isActive
                  ? 'bg-emerald-800 text-white shadow-sm'
                  : 'text-stone-600 hover:bg-stone-100 hover:text-stone-900'
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* ================= TAB 1: OVERVIEW & ANALYTICS ================= */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* KPI Stat Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              title="Registered Applications"
              value={metrics?.total_applications ?? '—'}
              subtitle={`${metrics?.draft_applications || 0} pending documentation`}
              icon={FileText}
            />
            <StatCard
              title="Portal Submitted"
              value={metrics?.submitted_applications ?? '—'}
              subtitle={`${metrics?.feasibility_approved || 0} technical feasibility approved`}
              icon={Landmark}
            />
            <StatCard
              title="Approved Subsidy (CFA)"
              value={formatCurrency(metrics?.approved_subsidy_total)}
              subtitle={`${metrics?.approved_applications || 0} applications sanctioned by govt`}
              icon={ShieldCheck}
            />
            <StatCard
              title="DBT Disbursed to Customers"
              value={formatCurrency(metrics?.disbursed_subsidy_total)}
              subtitle={`${metrics?.disbursed_applications || 0} claims credited to bank accounts`}
              icon={Wallet}
            />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Conversion Funnel */}
            <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
              <h3 className="text-base font-bold text-stone-900 flex items-center gap-2">
                <Landmark className="h-4 w-4 text-emerald-600" />
                Official Subsidy Lifecycle Funnel
              </h3>
              <p className="mt-1 text-xs text-stone-500">
                Tracking progression from internal documentation to official DBT bank credit
              </p>
              <div className="mt-6 h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={metrics?.conversion_funnel || []} layout="vertical" margin={{ left: 40, right: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f0f0f0" />
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis dataKey="stage" type="category" tick={{ fontSize: 10 }} width={130} />
                    <Tooltip formatter={(value) => [`${value} Applications`, 'Count']} />
                    <Bar dataKey="count" fill="#10b981" radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Financial Reconciliation */}
            <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
              <h3 className="text-base font-bold text-stone-900 flex items-center gap-2">
                <IndianRupee className="h-4 w-4 text-blue-600" />
                Financial Assistance Accounting
              </h3>
              <p className="mt-1 text-xs text-stone-500">
                Separating estimated claims, official sanctions, and actual DBT disbursements
              </p>
              <div className="mt-6 space-y-4">
                <div className="rounded-xl border border-stone-100 bg-stone-50 p-4">
                  <div className="flex justify-between items-center text-sm">
                    <span className="font-medium text-stone-600">Total Estimated Assistance:</span>
                    <span className="font-bold text-stone-900">{formatCurrency(metrics?.estimated_subsidy_total)}</span>
                  </div>
                  <div className="mt-2 h-2 rounded-full bg-stone-200 overflow-hidden">
                    <div className="h-full bg-stone-500 rounded-full" style={{ width: '100%' }} />
                  </div>
                </div>

                <div className="rounded-xl border border-blue-100 bg-blue-50/50 p-4">
                  <div className="flex justify-between items-center text-sm">
                    <span className="font-medium text-blue-800">Govt Sanctioned / Approved:</span>
                    <span className="font-bold text-blue-900">{formatCurrency(metrics?.approved_subsidy_total)}</span>
                  </div>
                  <div className="mt-2 h-2 rounded-full bg-blue-100 overflow-hidden">
                    <div
                      className="h-full bg-blue-600 rounded-full"
                      style={{
                        width: `${metrics?.estimated_subsidy_total ? Math.min(100, ((metrics?.approved_subsidy_total || 0) / metrics.estimated_subsidy_total) * 100) : 0}%`,
                      }}
                    />
                  </div>
                </div>

                <div className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-4">
                  <div className="flex justify-between items-center text-sm">
                    <span className="font-medium text-emerald-800">Directly Disbursed (DBT):</span>
                    <span className="font-bold text-emerald-950">{formatCurrency(metrics?.disbursed_subsidy_total)}</span>
                  </div>
                  <div className="mt-2 h-2 rounded-full bg-emerald-100 overflow-hidden">
                    <div
                      className="h-full bg-emerald-600 rounded-full"
                      style={{
                        width: `${metrics?.approved_subsidy_total ? Math.min(100, ((metrics?.disbursed_subsidy_total || 0) / metrics.approved_subsidy_total) * 100) : 0}%`,
                      }}
                    />
                  </div>
                </div>

                <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 flex items-start gap-2">
                  <Info className="h-4 w-4 shrink-0 text-amber-600 mt-0.5" />
                  <span>
                    <strong>Notice:</strong> Central financial assistance under PM Surya Ghar is disbursed directly by the Government of India into customer Aadhaar-seeded bank accounts and is never recorded as revenue of AARKA.
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ================= TAB 2: AVAILABLE GOVERNMENT SCHEMES ================= */}
      {activeTab === 'schemes' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-stone-900">Government Schemes Catalogue</h2>
              <p className="text-xs text-stone-500">
                Verified national, agricultural, and state solar subsidy schemes with regulatory references
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-stone-500">Filter:</span>
              <select
                value={schemeCategoryFilter}
                onChange={(e) => setSchemeCategoryFilter(e.target.value)}
                className={inputClass}
                style={{ width: 'auto' }}
              >
                <option value="ALL">All Categories</option>
                <option value="RESIDENTIAL">Residential (PM Surya Ghar)</option>
                <option value="GHS_RWA">Group Housing Society / RWA</option>
                <option value="AGRICULTURAL">Agricultural (PM-KUSUM)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {schemes
              .filter((s) => schemeCategoryFilter === 'ALL' || s.category === schemeCategoryFilter)
              .map((sch) => {
                const rule = sch.rules && sch.rules[0];
                const isVerified = sch.verification_status === 'OFFICIALLY_VERIFIED';
                return (
                  <div
                    key={sch.code}
                    className="flex flex-col rounded-2xl border border-stone-200 bg-white p-6 shadow-sm hover:shadow-md transition"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-md bg-stone-100 text-stone-700">
                        {sch.category} · {sch.jurisdiction}
                      </span>
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                          isVerified ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {isVerified ? 'Officially Verified' : 'Requires Confirmation'}
                      </span>
                    </div>

                    <h3 className="mt-3 text-base font-bold text-stone-900">{sch.name}</h3>
                    <p className="mt-1 text-xs text-stone-500 line-clamp-3">{sch.description}</p>

                    <div className="mt-4 rounded-xl bg-stone-50 p-3 space-y-1.5 text-xs">
                      <div className="flex justify-between">
                        <span className="text-stone-500">Authority:</span>
                        <span className="font-medium text-stone-800 text-right truncate max-w-[180px]">{sch.authority}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-stone-500">Max Assistance:</span>
                        <span className="font-bold text-emerald-700">
                          {rule?.maximum_assistance ? formatCurrency(rule.maximum_assistance) : 'State GBI / PPA'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-stone-500">Last Verified:</span>
                        <span className="text-stone-600">{formatDate(sch.last_verified_at)}</span>
                      </div>
                    </div>

                    <div className="mt-auto pt-5 flex items-center justify-between border-t border-stone-100">
                      <a
                        href={sch.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs font-semibold text-emerald-700 hover:text-emerald-900 flex items-center gap-1"
                      >
                        Official Portal <ExternalLink className="h-3 w-3" />
                      </a>
                      <button
                        onClick={() => openSchemeModal(sch)}
                        className="text-xs font-semibold text-stone-700 bg-stone-100 hover:bg-stone-200 px-3 py-1.5 rounded-lg transition"
                      >
                        View Rules & Checklist
                      </button>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* ================= TAB 3: CHECK ELIGIBILITY WIZARD ================= */}
      {activeTab === 'eligibility' && (
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="text-center">
            <h2 className="text-xl font-bold text-stone-900">Solar Subsidy Eligibility Checker</h2>
            <p className="mt-1 text-sm text-stone-500">
              Evaluate qualifications under official MNRE PM Surya Ghar & PM-KUSUM guidelines
            </p>
          </div>

          {/* Stepper Header */}
          <div className="flex items-center justify-between border-b border-stone-200 pb-4">
            {[
              { num: 1, label: 'Applicant Details' },
              { num: 2, label: 'Electricity Meter' },
              { num: 3, label: 'Roof & Capacity' },
              { num: 4, label: 'Review & Result' },
            ].map((s) => (
              <div
                key={s.num}
                className={`flex items-center gap-2 cursor-pointer ${
                  wizardStep === s.num ? 'text-emerald-800 font-bold' : 'text-stone-400'
                }`}
                onClick={() => setWizardStep(s.num)}
              >
                <span
                  className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${
                    wizardStep === s.num
                      ? 'bg-emerald-800 text-white'
                      : wizardStep > s.num
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-stone-100 text-stone-500'
                  }`}
                >
                  {wizardStep > s.num ? '✓' : s.num}
                </span>
                <span className="text-xs hidden sm:inline">{s.label}</span>
              </div>
            ))}
          </div>

          <div className="rounded-2xl border border-stone-200 bg-white p-6 sm:p-8 shadow-sm">
            {/* Step 1 */}
            {wizardStep === 1 && (
              <div className="space-y-4">
                <h3 className="text-base font-bold text-stone-900">Step 1: Applicant & Location</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Customer Category *</label>
                    <select
                      value={eligibilityForm.customer_category}
                      onChange={(e) => setEligibilityForm({ ...eligibilityForm, customer_category: e.target.value })}
                      className={inputClass}
                    >
                      <option value="RESIDENTIAL">Individual Residential Homeowner</option>
                      <option value="GHS_RWA">Group Housing Society / RWA (Common Meter)</option>
                      <option value="COMMERCIAL">Commercial / Industrial (Not subsidized under DBT)</option>
                      <option value="AGRICULTURAL">Farmer / Agricultural (PM-KUSUM)</option>
                    </select>
                  </div>
                  <div>
                    <label className={labelClass}>State / UT *</label>
                    <select
                      value={eligibilityForm.state}
                      onChange={(e) => setEligibilityForm({ ...eligibilityForm, state: e.target.value })}
                      className={inputClass}
                    >
                      <option value="Telangana">Telangana (Prioritized)</option>
                      <option value="Uttar Pradesh">Uttar Pradesh (UPNEDA Add-on)</option>
                      <option value="Delhi">Delhi (Solar Policy GBI)</option>
                      <option value="Maharashtra">Maharashtra</option>
                      <option value="Karnataka">Karnataka</option>
                      <option value="Gujarat">Gujarat</option>
                      <option value="Rajasthan">Rajasthan</option>
                      <option value="Ladakh">Ladakh (Special Category State)</option>
                      <option value="Uttarakhand">Uttarakhand (Special Category State)</option>
                    </select>
                  </div>
                  <div>
                    <label className={labelClass}>Applicant Full Name</label>
                    <input
                      type="text"
                      placeholder="e.g. Ramesh Chandra"
                      value={eligibilityForm.applicant_name}
                      onChange={(e) => setEligibilityForm({ ...eligibilityForm, applicant_name: e.target.value })}
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label className={labelClass}>Contact Phone Number</label>
                    <input
                      type="tel"
                      placeholder="e.g. +91 98765 43210"
                      value={eligibilityForm.applicant_phone}
                      onChange={(e) => setEligibilityForm({ ...eligibilityForm, applicant_phone: e.target.value })}
                      className={inputClass}
                    />
                  </div>
                </div>

                <div className="mt-6 flex justify-end">
                  <button
                    type="button"
                    onClick={() => setWizardStep(2)}
                    className="inline-flex items-center gap-2 rounded-xl bg-emerald-800 px-5 py-2.5 text-xs font-semibold text-white hover:bg-emerald-900 transition"
                  >
                    Continue to Meter Details <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Step 2 */}
            {wizardStep === 2 && (
              <div className="space-y-4">
                <h3 className="text-base font-bold text-stone-900">Step 2: Electricity Connection Details</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Electricity DISCOM *</label>
                    <select
                      value={eligibilityForm.discom_name}
                      onChange={(e) => setEligibilityForm({ ...eligibilityForm, discom_name: e.target.value })}
                      className={inputClass}
                    >
                      <option value="TSSPDCL">TSSPDCL (Southern Power Telangana)</option>
                      <option value="TSNPDCL">TSNPDCL (Northern Power Telangana)</option>
                      <option value="UPPCL">UPPCL (Uttar Pradesh Power Corp)</option>
                      <option value="BSES_RAJDHANI">BSES Rajdhani (Delhi)</option>
                      <option value="MSEDCL">MSEDCL (Maharashtra State)</option>
                      <option value="BESCOM">BESCOM (Bangalore)</option>
                    </select>
                  </div>
                  <div>
                    <label className={labelClass}>Consumer Account Number / USCNO *</label>
                    <input
                      type="text"
                      placeholder="e.g. 100234567"
                      value={eligibilityForm.consumer_number}
                      onChange={(e) => setEligibilityForm({ ...eligibilityForm, consumer_number: e.target.value })}
                      className={inputClass}
                      required
                    />
                  </div>
                  <div>
                    <label className={labelClass}>Tariff Category</label>
                    <input
                      type="text"
                      value={eligibilityForm.tariff_category}
                      onChange={(e) => setEligibilityForm({ ...eligibilityForm, tariff_category: e.target.value })}
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label className={labelClass}>Sanctioned Load (kW)</label>
                    <input
                      type="number"
                      step="0.5"
                      value={eligibilityForm.sanctioned_load_kw}
                      onChange={(e) => setEligibilityForm({ ...eligibilityForm, sanctioned_load_kw: e.target.value })}
                      className={inputClass}
                    />
                  </div>
                </div>

                <div className="mt-6 flex justify-between">
                  <button
                    type="button"
                    onClick={() => setWizardStep(1)}
                    className="rounded-xl border border-stone-200 px-4 py-2 text-xs font-semibold text-stone-700 hover:bg-stone-50"
                  >
                    Back
                  </button>
                  <button
                    type="button"
                    onClick={() => setWizardStep(3)}
                    className="inline-flex items-center gap-2 rounded-xl bg-emerald-800 px-5 py-2.5 text-xs font-semibold text-white hover:bg-emerald-900 transition"
                  >
                    Continue to Roof Details <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Step 3 */}
            {wizardStep === 3 && (
              <div className="space-y-4">
                <h3 className="text-base font-bold text-stone-900">Step 3: Installation & Capacity</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Proposed Capacity (kW) *</label>
                    <input
                      type="number"
                      step="0.5"
                      min="1"
                      max="10"
                      value={eligibilityForm.proposed_capacity}
                      onChange={(e) => setEligibilityForm({ ...eligibilityForm, proposed_capacity: e.target.value })}
                      className={inputClass}
                    />
                    <span className="text-[11px] text-stone-500 mt-1 block">
                      Individual rooftop max subsidized capacity is 3.0 kW (up to ₹78,000).
                    </span>
                  </div>
                  <div>
                    <label className={labelClass}>Available Roof Area (sq. ft.)</label>
                    <input
                      type="number"
                      value={eligibilityForm.available_roof_area_sqft}
                      onChange={(e) => setEligibilityForm({ ...eligibilityForm, available_roof_area_sqft: e.target.value })}
                      className={inputClass}
                    />
                    <span className="text-[11px] text-stone-500 mt-1 block">
                      Approx. 80-100 sq.ft. required per 1 kW of solar panels.
                    </span>
                  </div>
                  <div>
                    <label className={labelClass}>Roof Surface Type</label>
                    <select
                      value={eligibilityForm.roof_type}
                      onChange={(e) => setEligibilityForm({ ...eligibilityForm, roof_type: e.target.value })}
                      className={inputClass}
                    >
                      <option value="RCC Flat Concrete">RCC Flat Concrete</option>
                      <option value="Tin / Metal Sheet">Tin / Metal Sheet</option>
                      <option value="Sloped Tile Roof">Sloped Tile Roof</option>
                    </select>
                  </div>
                  <div className="space-y-2 pt-4">
                    <label className="flex items-center gap-2 text-xs text-stone-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={eligibilityForm.has_roof_rights}
                        onChange={(e) => setEligibilityForm({ ...eligibilityForm, has_roof_rights: e.target.checked })}
                        className="rounded border-stone-300 text-emerald-800 focus:ring-emerald-500"
                      />
                      <span>Customer holds ownership / explicit roof rights</span>
                    </label>
                    <label className="flex items-center gap-2 text-xs text-stone-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={eligibilityForm.is_grid_connected}
                        onChange={(e) => setEligibilityForm({ ...eligibilityForm, is_grid_connected: e.target.checked })}
                        className="rounded border-stone-300 text-emerald-800 focus:ring-emerald-500"
                      />
                      <span>Active grid connection ready for bi-directional net-meter</span>
                    </label>
                    <label className="flex items-center gap-2 text-xs text-stone-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={eligibilityForm.prior_subsidy_claimed}
                        onChange={(e) => setEligibilityForm({ ...eligibilityForm, prior_subsidy_claimed: e.target.checked })}
                        className="rounded border-stone-300 text-emerald-800 focus:ring-emerald-500"
                      />
                      <span>Prior central solar subsidy already claimed on this meter</span>
                    </label>
                  </div>
                </div>

                <div className="mt-6 flex justify-between">
                  <button
                    type="button"
                    onClick={() => setWizardStep(2)}
                    className="rounded-xl border border-stone-200 px-4 py-2 text-xs font-semibold text-stone-700 hover:bg-stone-50"
                  >
                    Back
                  </button>
                  <button
                    type="button"
                    onClick={(e) => {
                      setWizardStep(4);
                      handleCheckEligibility(e);
                    }}
                    className="inline-flex items-center gap-2 rounded-xl bg-emerald-800 px-6 py-2.5 text-xs font-semibold text-white hover:bg-emerald-900 shadow-md transition"
                  >
                    Evaluate Eligibility Now <ShieldCheck className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Step 4: Result */}
            {wizardStep === 4 && (
              <div className="space-y-6">
                {assessing ? (
                  <div className="py-12 text-center text-stone-500">
                    <RefreshCw className="h-8 w-8 animate-spin mx-auto text-emerald-800" />
                    <p className="mt-3 text-sm">Evaluating criteria against official MNRE gazette rules...</p>
                  </div>
                ) : assessmentResult ? (
                  <div className="space-y-6">
                    <div
                      className={`rounded-2xl p-6 border ${
                        assessmentResult.is_eligible
                          ? 'bg-emerald-50/70 border-emerald-200 text-emerald-950'
                          : 'bg-red-50/70 border-red-200 text-red-950'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        {assessmentResult.is_eligible ? (
                          <CheckCircle className="h-7 w-7 text-emerald-600 shrink-0" />
                        ) : (
                          <XCircle className="h-7 w-7 text-red-600 shrink-0" />
                        )}
                        <div>
                          <span className="text-xs font-bold uppercase tracking-wider block opacity-75">
                            Preliminary Assessment Result
                          </span>
                          <h3 className="text-lg font-bold">
                            {assessmentResult.is_eligible ? 'Potentially Eligible' : 'Potentially Not Eligible'}
                          </h3>
                          <p className="mt-1 text-xs opacity-90">{assessmentResult.scheme_name}</p>
                        </div>
                      </div>

                      {/* Financial breakdown if eligible */}
                      {assessmentResult.is_eligible && (
                        <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-3 bg-white/80 backdrop-blur rounded-xl p-4 text-center">
                          <div>
                            <span className="text-[11px] text-stone-500 block">Central CFA</span>
                            <span className="text-base font-bold text-emerald-800">
                              {formatCurrency(assessmentResult.central_subsidy)}
                            </span>
                          </div>
                          <div>
                            <span className="text-[11px] text-stone-500 block">State Top-up</span>
                            <span className="text-base font-bold text-blue-700">
                              {formatCurrency(assessmentResult.state_subsidy)}
                            </span>
                          </div>
                          <div>
                            <span className="text-[11px] text-stone-500 block">Project Cost Est.</span>
                            <span className="text-base font-bold text-stone-800">
                              {formatCurrency(assessmentResult.estimated_project_cost)}
                            </span>
                          </div>
                          <div>
                            <span className="text-[11px] text-stone-500 block">Net Customer Outlay</span>
                            <span className="text-base font-bold text-stone-950">
                              {formatCurrency(assessmentResult.estimated_customer_outlay)}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Explanations & Conditions */}
                    <div className="space-y-3">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-stone-500">Evaluation Findings</h4>
                      <ul className="space-y-1.5 text-xs text-stone-700">
                        {assessmentResult.reasons.map((r, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <span className="text-emerald-600 font-bold">•</span>
                            <span>{r}</span>
                          </li>
                        ))}
                      </ul>

                      <h4 className="text-xs font-bold uppercase tracking-wider text-stone-500 pt-2">Compliance Conditions</h4>
                      <ul className="space-y-1.5 text-xs text-stone-700">
                        {assessmentResult.conditions.map((c, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <span className="text-stone-400 font-bold">•</span>
                            <span>{c}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Statutory Disclaimer */}
                    <div className="rounded-xl border border-stone-200 bg-stone-50 p-4 text-xs text-stone-600 flex items-start gap-2.5">
                      <Info className="h-4 w-4 text-stone-400 shrink-0 mt-0.5" />
                      <span>{assessmentResult.disclaimer}</span>
                    </div>

                    <div className="flex justify-between items-center pt-2">
                      <button
                        type="button"
                        onClick={() => setWizardStep(1)}
                        className="rounded-xl border border-stone-200 px-4 py-2 text-xs font-semibold text-stone-700 hover:bg-stone-50"
                      >
                        Start Over
                      </button>
                      {assessmentResult.is_eligible && (
                        <button
                          type="button"
                          onClick={() => {
                            setApplyForm({
                              ...applyForm,
                              category: eligibilityForm.customer_category,
                              state: eligibilityForm.state,
                              discom_name: eligibilityForm.discom_name,
                              consumer_number: eligibilityForm.consumer_number,
                              capacity_kw: eligibilityForm.proposed_capacity,
                              subsidy_amount: String(assessmentResult.estimated_subsidy),
                            });
                            setShowApplyModal(true);
                          }}
                          className="inline-flex items-center gap-2 rounded-xl bg-emerald-800 px-5 py-2.5 text-xs font-semibold text-white hover:bg-emerald-900 shadow-md transition"
                        >
                          Apply with this Assessment <ArrowRight className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>
                ) : null}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ================= TAB 4: SUBSIDY CALCULATOR ================= */}
      {activeTab === 'calculator' && (
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="text-center">
            <h2 className="text-xl font-bold text-stone-900">Interactive Solar Subsidy Calculator</h2>
            <p className="mt-1 text-sm text-stone-500">
              Calculate central and state financial assistance based on system capacity and category
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Inputs Panel */}
            <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm space-y-5">
              <h3 className="text-sm font-bold text-stone-900 flex items-center gap-2">
                <Sliders className="h-4 w-4 text-emerald-800" />
                Input Parameters
              </h3>

              <div>
                <label className={labelClass}>Customer Category</label>
                <select
                  value={calcInputs.category}
                  onChange={(e) => setCalcInputs({ ...calcInputs, category: e.target.value })}
                  className={inputClass}
                >
                  <option value="RESIDENTIAL">Residential (PM Surya Ghar)</option>
                  <option value="GHS_RWA">Group Housing Society / RWA</option>
                  <option value="AGRICULTURAL">Farmer (PM-KUSUM)</option>
                </select>
              </div>

              <div>
                <label className={labelClass}>State</label>
                <select
                  value={calcInputs.state}
                  onChange={(e) => setCalcInputs({ ...calcInputs, state: e.target.value })}
                  className={inputClass}
                >
                  <option value="Telangana">Telangana</option>
                  <option value="Uttar Pradesh">Uttar Pradesh (UPNEDA)</option>
                  <option value="Delhi">Delhi</option>
                  <option value="Ladakh">Ladakh (Special Category)</option>
                  <option value="Uttarakhand">Uttarakhand (Special Category)</option>
                </select>
              </div>

              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className={labelClass}>Capacity: {calcInputs.capacity_kw} kW</label>
                </div>
                <input
                  type="range"
                  min="1"
                  max={calcInputs.category === 'GHS_RWA' ? 500 : 10}
                  step="0.5"
                  value={calcInputs.capacity_kw}
                  onChange={(e) => setCalcInputs({ ...calcInputs, capacity_kw: parseFloat(e.target.value) })}
                  className="w-full accent-emerald-800 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-stone-400 mt-1">
                  <span>1 kW</span>
                  <span>{calcInputs.category === 'GHS_RWA' ? '500 kW' : '10 kW'}</span>
                </div>
              </div>
            </div>

            {/* Outputs Panel */}
            <div className="md:col-span-2 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-stone-100 pb-4">
                  <h3 className="text-sm font-bold text-stone-900">{calcOutput?.scheme_name || 'Subsidy Estimate'}</h3>
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800">
                    Max Cap: {formatCurrency(calcOutput?.max_subsidy_limit)}
                  </span>
                </div>

                {/* Big Metric Display */}
                <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="rounded-xl border border-emerald-100 bg-emerald-50/60 p-4 text-center">
                    <span className="text-xs font-medium text-emerald-800 block">Total Govt Assistance</span>
                    <span className="text-2xl font-black text-emerald-950 mt-1 block">
                      {formatCurrency(calcOutput?.total_subsidy)}
                    </span>
                    <span className="text-[10px] text-emerald-700 mt-1 block">Direct Bank Credit (DBT)</span>
                  </div>

                  <div className="rounded-xl border border-stone-100 bg-stone-50 p-4 text-center">
                    <span className="text-xs font-medium text-stone-600 block">Estimated Benchmark Cost</span>
                    <span className="text-xl font-bold text-stone-900 mt-1 block">
                      {formatCurrency(calcOutput?.estimated_cost)}
                    </span>
                    <span className="text-[10px] text-stone-400 mt-1 block">~₹60,000 / kW standard EPC</span>
                  </div>

                  <div className="rounded-xl border border-stone-100 bg-stone-50 p-4 text-center">
                    <span className="text-xs font-medium text-stone-600 block">Net Customer Contribution</span>
                    <span className="text-xl font-bold text-stone-900 mt-1 block">
                      {formatCurrency(calcOutput?.customer_contribution)}
                    </span>
                    <span className="text-[10px] text-stone-400 mt-1 block">After DBT reimbursement</span>
                  </div>
                </div>

                {/* Arithmetic Steps */}
                <div className="mt-6 space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-stone-400">Calculation Steps</h4>
                  <div className="rounded-xl border border-stone-100 bg-stone-50/50 p-3 space-y-1 text-xs font-mono text-stone-700">
                    {calcOutput?.calculation_steps?.map((step, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <span className="text-emerald-700 font-bold">›</span>
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <p className="mt-6 text-[11px] text-stone-400 leading-relaxed border-t border-stone-100 pt-3">
                * Note: Illustration only. The central subsidy is sanctioned by the National Portal following joint DISCOM inspection and commissioning.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ================= TAB 5: APPLICATION REGISTER ================= */}
      {activeTab === 'applications' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="relative w-72">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
                <input
                  type="search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search consumer, application #..."
                  className={`${inputClass} pl-9`}
                />
              </div>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className={`${inputClass} w-48`}
              >
                <option value="ALL">All Official Statuses</option>
                <option value="NOT_SUBMITTED">Not Submitted</option>
                <option value="SUBMITTED">Submitted to Portal</option>
                <option value="FEASIBILITY_APPROVED">Feasibility Approved</option>
                <option value="COMMISSIONED">Commissioned</option>
                <option value="APPROVED">Subsidy Approved</option>
                <option value="DISBURSED">DBT Disbursed</option>
                <option value="REJECTED">Rejected</option>
              </select>
            </div>

            <button
              onClick={() => setShowApplyModal(true)}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-800 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-900 transition"
            >
              <Plus className="h-4 w-4" />
              New Application
            </button>
          </div>

          <div className="rounded-2xl border border-stone-200 bg-white overflow-hidden shadow-sm">
            <DataTable
              columns={columns}
              data={filteredApps}
              loading={loading}
              emptyMessage="No subsidy applications found matching criteria."
            />
          </div>
        </div>
      )}

      {/* ================= TAB 6: CUSTOMER TRACKER ================= */}
      {activeTab === 'tracker' && (
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="text-center">
            <h2 className="text-xl font-bold text-stone-900">Customer Subsidy Application Tracker</h2>
            <p className="mt-1 text-sm text-stone-500">
              Track the exact 12-stage milestone status of your PM Surya Ghar application
            </p>
          </div>

          {/* Search Box */}
          <form onSubmit={handleTrackSearch} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
              <input
                type="text"
                placeholder="Enter Application Number (e.g. SUB-2026-XXXXX) or National Portal Ref..."
                value={trackerSearch}
                onChange={(e) => setTrackerSearch(e.target.value)}
                className={`${inputClass} pl-10 py-3 text-sm`}
                required
              />
            </div>
            <button
              type="submit"
              disabled={trackingLoading}
              className="rounded-xl bg-emerald-800 px-6 py-3 text-xs font-bold text-white hover:bg-emerald-900 transition flex items-center gap-2"
            >
              {trackingLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : 'Track Status'}
            </button>
          </form>

          {trackingError && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-xs text-red-800 flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-600 shrink-0" />
              <span>{trackingError}</span>
            </div>
          )}

          {trackedApplication && (
            <div className="rounded-2xl border border-stone-200 bg-white p-6 sm:p-8 shadow-sm space-y-6">
              {/* Top Summary Card */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-stone-100 pb-6 gap-4">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-md">
                    {trackedApplication.category} · {trackedApplication.capacity_kw} kW
                  </span>
                  <h3 className="mt-2 text-lg font-bold text-stone-900">{trackedApplication.customer_name}</h3>
                  <p className="text-xs text-stone-500">
                    DISCOM: {trackedApplication.discom} · Ref: <span className="font-mono text-stone-700">{trackedApplication.portal_reference}</span>
                  </p>
                </div>

                <div className="text-left sm:text-right">
                  <span className="text-xs text-stone-400 block">Sanctioned Assistance (DBT)</span>
                  <span className="text-2xl font-black text-emerald-800">
                    {formatCurrency(trackedApplication.disbursed_subsidy > 0 ? trackedApplication.disbursed_subsidy : trackedApplication.estimated_subsidy)}
                  </span>
                  <span className="text-[10px] font-semibold text-stone-500 block mt-0.5">
                    Status: <StatusBadge status={trackedApplication.official_status || trackedApplication.internal_status} />
                  </span>
                </div>
              </div>

              {/* 12-Stage Timeline */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-stone-500">Milestone Timeline</h4>
                <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-stone-200">
                  {trackedApplication.timeline?.map((stg, idx) => {
                    const isDone = stg.status === 'COMPLETED';
                    const isCurr = stg.status === 'CURRENT';
                    return (
                      <div key={idx} className="relative flex items-start gap-4">
                        <span
                          className={`absolute -left-6 flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${
                            isDone
                              ? 'bg-emerald-600 text-white'
                              : isCurr
                              ? 'bg-amber-500 text-white ring-4 ring-amber-100'
                              : 'bg-stone-200 text-stone-500'
                          }`}
                        >
                          {isDone ? '✓' : idx + 1}
                        </span>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <span className={`text-xs font-bold ${isDone ? 'text-stone-900' : isCurr ? 'text-amber-800' : 'text-stone-400'}`}>
                              {stg.stage}
                            </span>
                            <span className="text-[10px] font-semibold text-stone-400">
                              By: {stg.responsible_party}
                            </span>
                          </div>
                          <p className="text-[11px] text-stone-500 mt-0.5">{stg.description}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ================= MODAL: REGISTER NEW APPLICATION ================= */}
      <Modal
        isOpen={showApplyModal}
        onClose={() => setShowApplyModal(false)}
        title="Register Government Subsidy Application"
      >
        <form onSubmit={handleCreateApplication} className="space-y-4">
          <div>
            <label className={labelClass}>Customer *</label>
            <select
              value={applyForm.customer_id}
              onChange={(e) => setApplyForm({ ...applyForm, customer_id: e.target.value })}
              className={inputClass}
              required
            >
              <option value="">Select Existing Customer</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.phone || c.email})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelClass}>Category</label>
              <select
                value={applyForm.category}
                onChange={(e) => setApplyForm({ ...applyForm, category: e.target.value })}
                className={inputClass}
              >
                <option value="RESIDENTIAL">Residential (PM Surya Ghar)</option>
                <option value="GHS_RWA">Group Housing Society</option>
                <option value="AGRICULTURAL">PM-KUSUM Farmer</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Capacity (kW)</label>
              <input
                type="number"
                step="0.5"
                value={applyForm.capacity_kw}
                onChange={(e) => setApplyForm({ ...applyForm, capacity_kw: e.target.value })}
                className={inputClass}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelClass}>State</label>
              <input
                type="text"
                value={applyForm.state}
                onChange={(e) => setApplyForm({ ...applyForm, state: e.target.value })}
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>DISCOM</label>
              <input
                type="text"
                value={applyForm.discom_name}
                onChange={(e) => setApplyForm({ ...applyForm, discom_name: e.target.value })}
                className={inputClass}
              />
            </div>
          </div>

          <div>
            <label className={labelClass}>Consumer Number / USCNO *</label>
            <input
              type="text"
              placeholder="e.g. 100234567"
              value={applyForm.consumer_number}
              onChange={(e) => setApplyForm({ ...applyForm, consumer_number: e.target.value })}
              className={inputClass}
              required
            />
          </div>

          <div>
            <label className={labelClass}>Internal Remarks</label>
            <textarea
              rows={2}
              value={applyForm.remarks}
              onChange={(e) => setApplyForm({ ...applyForm, remarks: e.target.value })}
              className={inputClass}
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowApplyModal(false)}
              className="rounded-xl border border-stone-200 px-4 py-2 text-xs font-semibold text-stone-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-xl bg-emerald-800 px-5 py-2 text-xs font-semibold text-white hover:bg-emerald-900"
            >
              Submit Application
            </button>
          </div>
        </form>
      </Modal>

      {/* ================= MODAL: SCHEME DETAILS & CHECKLIST ================= */}
      {selectedScheme && (
        <Modal
          isOpen={!!selectedScheme}
          onClose={() => setSelectedScheme(null)}
          title={selectedScheme.name}
        >
          <div className="space-y-5">
            <div className="rounded-xl bg-stone-50 p-4 space-y-2 text-xs">
              <p className="text-stone-700 leading-relaxed">{selectedScheme.description}</p>
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-stone-200">
                <div>
                  <span className="text-stone-400 block">Authority:</span>
                  <span className="font-semibold text-stone-800">{selectedScheme.authority}</span>
                </div>
                <div>
                  <span className="text-stone-400 block">Notification Ref:</span>
                  <span className="font-mono text-stone-800">{selectedScheme.notification_reference || 'N/A'}</span>
                </div>
              </div>
            </div>

            {/* Checklist */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-stone-500 mb-2">
                Mandatory Document Checklist by Stage
              </h4>
              <div className="space-y-3">
                {schemeChecklist?.stages?.map((stg, i) => (
                  <div key={i} className="rounded-xl border border-stone-100 bg-white p-3 space-y-1.5">
                    <span className="text-[11px] font-bold text-emerald-800 block uppercase">
                      {stg.stage.replace(/_/g, ' ')}
                    </span>
                    <ul className="text-xs text-stone-600 space-y-1">
                      {stg.documents?.map((d, j) => (
                        <li key={j} className="flex items-center gap-2">
                          <Check className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                          <span>{d.name}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedScheme(null)}
                className="rounded-xl border border-stone-200 px-4 py-2 text-xs font-semibold text-stone-700"
              >
                Close
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* ================= DRAWER: APPLICATION DETAIL & REVIEW ================= */}
      {selectedApplication && (
        <Modal
          isOpen={!!selectedApplication}
          onClose={() => setSelectedApplication(null)}
          title={`Application Details: ${selectedApplication.application_number}`}
        >
          <div className="space-y-6">
            {/* Header info */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-stone-100 pb-4 gap-2">
              <div>
                <span className="text-xs text-stone-400 font-mono">
                  Portal Ref: {selectedApplication.portal_application_ref || 'Pending'}
                </span>
                <h3 className="text-base font-bold text-stone-900">{selectedApplication.customer_name}</h3>
                <span className="text-xs text-stone-500">
                  {selectedApplication.discom_name} · Consumer #{selectedApplication.consumer_number}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowOfficialUpdateModal(true)}
                  className="rounded-xl bg-blue-50 border border-blue-200 text-blue-800 px-3 py-1.5 text-xs font-bold hover:bg-blue-100"
                >
                  Update Official Status
                </button>
              </div>
            </div>

            {/* Document Collection Desk */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-stone-500">
                  Compliance Documents & Verification (Level 2)
                </h4>
                <button
                  onClick={() => setShowDocUploadModal(true)}
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-800 hover:text-emerald-950"
                >
                  <Upload className="h-3.5 w-3.5" /> Upload Document
                </button>
              </div>

              {appDocuments.length === 0 ? (
                <div className="rounded-xl border border-dashed border-stone-200 p-6 text-center text-xs text-stone-400">
                  No documents uploaded yet for this application.
                </div>
              ) : (
                <div className="space-y-2">
                  {appDocuments.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex flex-col sm:flex-row sm:items-center justify-between rounded-xl border border-stone-100 bg-stone-50 p-3 gap-2"
                    >
                      <div>
                        <span className="text-xs font-bold text-stone-900 block">{doc.document_type.replace(/_/g, ' ')}</span>
                        <span className="text-[11px] text-stone-500">
                          {doc.original_filename} · v{doc.version_number}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        <StatusBadge status={doc.review_status} />
                        {doc.review_status !== 'VERIFIED_BY_AARKA' && (
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => handleReviewDocument(doc.id, 'VERIFIED')}
                              className="px-2 py-1 rounded bg-emerald-600 text-white text-[10px] font-bold hover:bg-emerald-700"
                            >
                              Verify
                            </button>
                            <button
                              onClick={() => handleReviewDocument(doc.id, 'REJECTED', 'Clear copy required')}
                              className="px-2 py-1 rounded bg-red-600 text-white text-[10px] font-bold hover:bg-red-700"
                            >
                              Reject
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* History timeline */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-stone-500 mb-3">Audit Log & Milestones</h4>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {appHistory.map((h) => (
                  <div key={h.id} className="text-xs border-l-2 border-stone-200 pl-3 py-1">
                    <div className="flex justify-between text-stone-400 text-[10px]">
                      <span>{h.updated_by} ({h.actor_type})</span>
                      <span>{formatDate(h.created_at)}</span>
                    </div>
                    <span className="font-semibold text-stone-800">{h.new_status}</span>
                    <p className="text-stone-500 text-[11px]">{h.remarks}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* ================= MODAL: DOCUMENT UPLOAD ================= */}
      {showDocUploadModal && (
        <Modal
          isOpen={showDocUploadModal}
          onClose={() => setShowDocUploadModal(false)}
          title="Upload Subsidy Document"
        >
          <form onSubmit={handleUploadDocument} className="space-y-4">
            <div>
              <label className={labelClass}>Document Type *</label>
              <select
                value={uploadDocType}
                onChange={(e) => setUploadDocType(e.target.value)}
                className={inputClass}
              >
                <option value="ELECTRICITY_BILL">Latest Electricity Bill (with USCNO)</option>
                <option value="PROPERTY_TAX_OR_ROOF_CONSENT">Roof Ownership / Property Tax Receipt</option>
                <option value="AADHAAR_CARD">Aadhaar Card (Connection Holder)</option>
                <option value="BANK_PASSBOOK_OR_CHEQUE">Cancelled Cheque / Bank Passbook (for DBT)</option>
                <option value="INSTALLATION_PHOTO">Geo-tagged Installation Photos</option>
                <option value="NET_METER_REPORT">Net-Meter Test Report</option>
                <option value="COMMISSIONING_CERTIFICATE">Joint Commissioning Certificate (JCC)</option>
              </select>
            </div>

            <div>
              <label className={labelClass}>Choose File (PDF, JPG, PNG up to 10MB) *</label>
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.webp"
                onChange={(e) => setUploadFile(e.target.files[0])}
                className={inputClass}
                required
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowDocUploadModal(false)}
                className="rounded-xl border border-stone-200 px-4 py-2 text-xs font-semibold text-stone-700"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={uploading}
                className="rounded-xl bg-emerald-800 px-5 py-2 text-xs font-semibold text-white hover:bg-emerald-900"
              >
                {uploading ? 'Uploading...' : 'Upload & Validate'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* ================= MODAL: OFFICIAL STATUS UPDATE ================= */}
      {showOfficialUpdateModal && (
        <Modal
          isOpen={showOfficialUpdateModal}
          onClose={() => setShowOfficialUpdateModal(false)}
          title="Record Official Government / DISCOM Milestone"
        >
          <form onSubmit={handleUpdateOfficialStatus} className="space-y-4">
            <div>
              <label className={labelClass}>Official Government Stage *</label>
              <select
                value={officialStatusForm.official_status}
                onChange={(e) => setOfficialStatusForm({ ...officialStatusForm, official_status: e.target.value })}
                className={inputClass}
              >
                <option value="SUBMITTED">Submitted to National Portal</option>
                <option value="FEASIBILITY_APPROVED">DISCOM Technical Feasibility Approved</option>
                <option value="FEASIBILITY_REJECTED">DISCOM Feasibility Rejected</option>
                <option value="INSTALLED">Installation Completed by EPC</option>
                <option value="INSPECTION_PENDING">Net-Meter Joint Inspection Pending</option>
                <option value="COMMISSIONED">System Commissioned (JCC Issued)</option>
                <option value="SUBSIDY_CLAIM_PENDING">Subsidy Claim Submitted</option>
                <option value="APPROVED">Subsidy Sanctioned / Approved</option>
                <option value="DISBURSED">Subsidy Disbursed via DBT</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelClass}>National Portal Ref</label>
                <input
                  type="text"
                  placeholder="e.g. PMSG-2026-98123"
                  value={officialStatusForm.portal_application_ref}
                  onChange={(e) => setOfficialStatusForm({ ...officialStatusForm, portal_application_ref: e.target.value })}
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Evidence / Order Ref</label>
                <input
                  type="text"
                  placeholder="e.g. TSSPDCL/SANCTION/042"
                  value={officialStatusForm.evidence_reference}
                  onChange={(e) => setOfficialStatusForm({ ...officialStatusForm, evidence_reference: e.target.value })}
                  className={inputClass}
                />
              </div>
            </div>

            {officialStatusForm.official_status === 'DISBURSED' && (
              <div className="grid grid-cols-2 gap-3 bg-emerald-50 p-3 rounded-xl border border-emerald-100">
                <div>
                  <label className={labelClass}>Disbursed Amount (₹)</label>
                  <input
                    type="number"
                    value={officialStatusForm.disbursed_amount}
                    onChange={(e) => setOfficialStatusForm({ ...officialStatusForm, disbursed_amount: e.target.value })}
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className={labelClass}>DBT Payment Reference</label>
                  <input
                    type="text"
                    placeholder="PFMS/DBT/2026/..."
                    value={officialStatusForm.disbursement_reference}
                    onChange={(e) => setOfficialStatusForm({ ...officialStatusForm, disbursement_reference: e.target.value })}
                    className={inputClass}
                  />
                </div>
              </div>
            )}

            <div>
              <label className={labelClass}>Official Remarks</label>
              <textarea
                rows={2}
                value={officialStatusForm.remarks}
                onChange={(e) => setOfficialStatusForm({ ...officialStatusForm, remarks: e.target.value })}
                className={inputClass}
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowOfficialUpdateModal(false)}
                className="rounded-xl border border-stone-200 px-4 py-2 text-xs font-semibold text-stone-700"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="rounded-xl bg-blue-700 px-5 py-2 text-xs font-semibold text-white hover:bg-blue-800"
              >
                Save Milestone
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
