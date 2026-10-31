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
  Compass,
  Home,
  Tractor,
  Building,
  CheckCheck,
  Award,
  Zap,
  TrendingUp,
  SlidersHorizontal,
  ChevronDown,
  Filter
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
  { id: 'overview', label: 'Overview & Insights', icon: Landmark },
  { id: 'schemes', label: 'Government Schemes', icon: Layers },
  { id: 'eligibility', label: 'Check Eligibility', icon: ShieldCheck },
  { id: 'calculator', label: 'Subsidy Calculator', icon: Calculator },
  { id: 'applications', label: 'Application Register', icon: FileText },
  { id: 'tracker', label: 'Track Application', icon: Compass },
];

const SCHEME_PALETTE = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#06b6d4', '#ec4899'];

const formatCurrency = (val) =>
  `₹${Number(val || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

const formatDate = (val) => {
  if (!val) return '—';
  const d = new Date(val);
  if (Number.isNaN(d.getTime())) return val;
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
};

const inputClass =
  'w-full rounded-xl border border-stone-200 bg-white px-3.5 py-2.5 text-xs text-stone-800 outline-none transition placeholder:text-stone-400 focus:border-emerald-600 focus:ring-4 focus:ring-emerald-500/10 shadow-xs';

const labelClass = 'block text-[11px] font-bold text-stone-600 mb-1.5 uppercase tracking-wider';

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
  const [appDrawerTab, setAppDrawerTab] = useState('details');

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
    if (e) e.preventDefault();
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
    setAppDrawerTab('details');
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
      header: 'Application & Portal Ref',
      accessor: (row) => (
        <div>
          <span className="font-bold text-stone-900 block text-xs">{row.application_number}</span>
          <span className="text-[11px] text-emerald-800 font-mono font-medium flex items-center gap-1 mt-0.5">
            <Landmark className="h-3 w-3 shrink-0" />
            {row.portal_application_ref || 'Pending Portal Ref'}
          </span>
        </div>
      ),
    },
    {
      header: 'Applicant & Electricity Meter',
      accessor: (row) => (
        <div>
          <span className="font-semibold text-stone-800 block text-xs">{row.customer_name || '—'}</span>
          <span className="text-[11px] text-stone-500 flex items-center gap-1 mt-0.5">
            <Zap className="h-3 w-3 text-amber-500 shrink-0" />
            {row.discom_name} · USC: <span className="font-mono">{row.consumer_number || 'N/A'}</span>
          </span>
        </div>
      ),
    },
    {
      header: 'System Scale',
      accessor: (row) => (
        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-stone-700 bg-stone-100 border border-stone-200/80 px-2 py-1 rounded-lg">
          {row.capacity_kw} kW · {row.category}
        </span>
      ),
    },
    {
      header: 'AARKA Verification',
      accessor: (row) => (
        <StatusBadge status={row.internal_status || row.verification_status || 'DRAFT'} />
      ),
    },
    {
      header: 'National Portal Status',
      accessor: (row) => (
        <StatusBadge status={row.official_status || row.approval_status || 'NOT_SUBMITTED'} />
      ),
    },
    {
      header: 'Government Grant (DBT)',
      accessor: (row) => (
        <div>
          <span className="font-black text-emerald-800 block text-xs">
            {formatCurrency(row.disbursed_amount > 0 ? row.disbursed_amount : (row.approved_amount > 0 ? row.approved_amount : row.subsidy_amount))}
          </span>
          <span className="text-[10px] uppercase font-bold text-stone-400 block tracking-wider">
            {row.disbursed_amount > 0 ? '✓ DBT Credited' : (row.approved_amount > 0 ? 'Sanctioned' : 'Estimated')}
          </span>
        </div>
      ),
    },
    {
      header: 'Desk Action',
      accessor: (row) => (
        <button
          onClick={() => openAppDrawer(row)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-stone-200/90 bg-white text-xs font-bold text-stone-800 hover:bg-stone-50 hover:border-emerald-500 shadow-xs transition"
        >
          <Eye className="h-3.5 w-3.5 text-emerald-600" />
          Review & Track
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6 pb-16">
      {/* ================= HERO SECTION ================= */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#071b12] via-[#0b2519] to-[#143e2b] p-6 text-white shadow-2xl sm:p-8 border border-emerald-900/40">
        <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-emerald-500/15 border border-emerald-400/25 px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-emerald-300 backdrop-blur-md">
              <Landmark className="h-3.5 w-3.5 text-emerald-400" />
              <span>National Solar Mission · PM Surya Ghar & PM-KUSUM</span>
            </div>

            <h1 className="mt-3 text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-white font-display">
              Government Solar Subsidies & Governance Desk
            </h1>

            <p className="mt-2.5 text-xs sm:text-sm text-stone-300 leading-relaxed max-w-2xl">
              Seamlessly discover central and state government rooftop solar assistance, perform preliminary eligibility validations, manage compliance documents with 3-level verification, and monitor direct beneficiary transfers (DBT) credited by PFMS.
            </p>

            {/* Quick Policy Badges */}
            <div className="mt-5 flex flex-wrap items-center gap-2 text-xs">
              <span className="inline-flex items-center gap-1.5 rounded-lg bg-white/10 px-2.5 py-1 text-emerald-200 border border-white/10 backdrop-blur-sm">
                <Check className="h-3.5 w-3.5 text-emerald-400" /> Up to ₹78,000 Residential DBT
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-lg bg-white/10 px-2.5 py-1 text-blue-200 border border-white/10 backdrop-blur-sm">
                <Building className="h-3.5 w-3.5 text-blue-400" /> ₹18,000/kW for Housing Societies
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-lg bg-white/10 px-2.5 py-1 text-amber-200 border border-white/10 backdrop-blur-sm">
                <Tractor className="h-3.5 w-3.5 text-amber-400" /> PM-KUSUM Farmer Grants
              </span>
            </div>
          </div>

          <div className="flex flex-wrap lg:flex-col items-stretch sm:items-end gap-3 shrink-0">
            <button
              onClick={() => setActiveTab('eligibility')}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 px-5 py-2.5 text-xs font-bold text-white shadow-lg shadow-emerald-500/25 transition hover:from-emerald-600 hover:to-emerald-700 active:scale-95"
            >
              <ShieldCheck className="h-4 w-4" />
              Check Eligibility (Instant)
            </button>
            <div className="flex items-center gap-2">
              <button
                onClick={loadData}
                disabled={refreshing}
                className="inline-flex items-center gap-1.5 rounded-xl bg-white/10 border border-white/15 px-3 py-2 text-xs font-semibold text-white backdrop-blur-md transition hover:bg-white/20"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              <button
                onClick={() => setShowApplyModal(true)}
                className="inline-flex items-center gap-1.5 rounded-xl bg-white text-stone-900 px-4 py-2 text-xs font-bold shadow-md transition hover:bg-stone-100"
              >
                <Plus className="h-3.5 w-3.5 text-emerald-700" />
                Register Application
              </button>
            </div>
          </div>
        </div>

        {/* Ambient Glow Orbs */}
        <div className="pointer-events-none absolute -right-12 -top-12 h-64 w-64 rounded-full bg-emerald-500/20 blur-3xl" />
        <div className="pointer-events-none absolute -left-12 -bottom-12 h-48 w-48 rounded-full bg-amber-500/10 blur-2xl" />
      </div>

      {/* Notifications */}
      {errorMsg && (
        <div className="flex items-center gap-3 rounded-2xl border border-red-200 bg-red-50/90 p-4 text-xs font-medium text-red-900 shadow-sm">
          <AlertCircle className="h-5 w-5 shrink-0 text-red-600" />
          <span className="flex-1">{errorMsg}</span>
          <button onClick={() => setErrorMsg('')} className="text-red-500 hover:text-red-800">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
      {successMsg && (
        <div className="flex items-center gap-3 rounded-2xl border border-emerald-200 bg-emerald-50/90 p-4 text-xs font-medium text-emerald-900 shadow-sm">
          <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600" />
          <span className="flex-1">{successMsg}</span>
          <button onClick={() => setSuccessMsg('')} className="text-emerald-600 hover:text-emerald-900">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* ================= MODERN TAB BAR ================= */}
      <div className="flex items-center gap-1 overflow-x-auto rounded-2xl border border-stone-200/80 bg-stone-100/70 p-1.5 backdrop-blur-md">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 whitespace-nowrap rounded-xl px-4 py-2.5 text-xs font-bold transition duration-150 ${
                isActive
                  ? 'bg-white text-emerald-950 shadow-sm scale-[1.01] border border-stone-200/50'
                  : 'text-stone-600 hover:bg-stone-200/60 hover:text-stone-900'
              }`}
            >
              <Icon className={`h-4 w-4 ${isActive ? 'text-emerald-600' : 'text-stone-400'}`} />
              {tab.label}
              {tab.id === 'applications' && subsidies.length > 0 && (
                <span className={`ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold ${isActive ? 'bg-emerald-100 text-emerald-800' : 'bg-stone-200 text-stone-600'}`}>
                  {subsidies.length}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* ================= TAB 1: OVERVIEW & INSIGHTS ================= */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Top 4 KPI Stat Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl border border-stone-200/80 bg-white p-5 shadow-xs hover:shadow-md transition">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider">Total Applications</span>
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-stone-100 text-stone-700">
                  <FileText className="h-5 w-5" />
                </div>
              </div>
              <p className="mt-3 text-2xl font-black text-stone-900">{metrics?.total_applications ?? '—'}</p>
              <p className="mt-1 text-[11px] text-stone-500 flex items-center gap-1">
                <Clock3 className="h-3 w-3 text-amber-500" />
                {metrics?.draft_applications || 0} applications in documentation phase
              </p>
            </div>

            <div className="rounded-2xl border border-stone-200/80 bg-white p-5 shadow-xs hover:shadow-md transition">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider">Submitted to Portal</span>
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
                  <Landmark className="h-5 w-5" />
                </div>
              </div>
              <p className="mt-3 text-2xl font-black text-blue-950">{metrics?.submitted_applications ?? '—'}</p>
              <p className="mt-1 text-[11px] text-blue-700 font-medium flex items-center gap-1">
                <Check className="h-3 w-3" />
                {metrics?.feasibility_approved || 0} DISCOM feasibility approved
              </p>
            </div>

            <div className="rounded-2xl border border-stone-200/80 bg-white p-5 shadow-xs hover:shadow-md transition">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider">Government Sanctioned</span>
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700">
                  <ShieldCheck className="h-5 w-5" />
                </div>
              </div>
              <p className="mt-3 text-2xl font-black text-emerald-950">{formatCurrency(metrics?.approved_subsidy_total)}</p>
              <p className="mt-1 text-[11px] text-emerald-800 font-medium">
                {metrics?.approved_applications || 0} applications approved by ministry
              </p>
            </div>

            <div className="rounded-2xl border border-stone-200/80 bg-white p-5 shadow-xs hover:shadow-md transition">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider">Disbursed to Bank (DBT)</span>
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-50 text-purple-700">
                  <Wallet className="h-5 w-5" />
                </div>
              </div>
              <p className="mt-3 text-2xl font-black text-purple-950">{formatCurrency(metrics?.disbursed_subsidy_total)}</p>
              <p className="mt-1 text-[11px] text-purple-800 font-medium flex items-center gap-1">
                <Award className="h-3 w-3 text-purple-600" />
                {metrics?.disbursed_applications || 0} direct bank credits confirmed
              </p>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Conversion Funnel */}
            <div className="rounded-2xl border border-stone-200/80 bg-white p-6 shadow-xs">
              <div className="flex items-center justify-between border-b border-stone-100 pb-3">
                <div>
                  <h3 className="text-sm font-bold text-stone-900 flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-emerald-600" />
                    Official Scheme Progression Funnel
                  </h3>
                  <p className="text-[11px] text-stone-500 mt-0.5">
                    Conversion through internal review, DISCOM sanction, and DBT disbursement
                  </p>
                </div>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-stone-100 text-stone-600">
                  Database Live
                </span>
              </div>

              <div className="mt-6 h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={metrics?.conversion_funnel || []} layout="vertical" margin={{ left: 50, right: 30 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f5f5f4" />
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis dataKey="stage" type="category" tick={{ fontSize: 10, fill: '#57534e' }} width={140} />
                    <Tooltip
                      contentStyle={{ borderRadius: 12, border: '1px solid #e7e5e4', fontSize: 12 }}
                      formatter={(val) => [`${val} Applications`, 'Count']}
                    />
                    <Bar dataKey="count" fill="#0b2519" radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Financial Ledger & Direct Transfer Accounting */}
            <div className="rounded-2xl border border-stone-200/80 bg-white p-6 shadow-xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-stone-100 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-stone-900 flex items-center gap-2">
                      <IndianRupee className="h-4 w-4 text-blue-600" />
                      Financial Assistance Reconciliation
                    </h3>
                    <p className="text-[11px] text-stone-500 mt-0.5">
                      Distinguishing preliminary estimates from government-disbursed funds
                    </p>
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-blue-50 text-blue-700">
                    Direct Beneficiary Transfer
                  </span>
                </div>

                <div className="mt-6 space-y-4">
                  {/* Estimated */}
                  <div className="rounded-xl border border-stone-100 bg-stone-50 p-3.5">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold text-stone-600">Total Estimated Assistance:</span>
                      <span className="font-bold text-stone-900">{formatCurrency(metrics?.estimated_subsidy_total)}</span>
                    </div>
                    <div className="mt-2 h-2 rounded-full bg-stone-200 overflow-hidden">
                      <div className="h-full bg-stone-600 rounded-full" style={{ width: '100%' }} />
                    </div>
                  </div>

                  {/* Approved */}
                  <div className="rounded-xl border border-blue-100 bg-blue-50/50 p-3.5">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold text-blue-900">Sanctioned by Ministry (CFA):</span>
                      <span className="font-bold text-blue-950">{formatCurrency(metrics?.approved_subsidy_total)}</span>
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

                  {/* Disbursed */}
                  <div className="rounded-xl border border-emerald-100 bg-emerald-50/60 p-3.5">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold text-emerald-950">Disbursed to Bank (DBT):</span>
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
                </div>
              </div>

              {/* Legal Notice */}
              <div className="mt-5 rounded-xl border border-amber-200/70 bg-amber-50/60 p-3 text-[11px] text-amber-900 flex items-start gap-2">
                <Info className="h-4 w-4 shrink-0 text-amber-600 mt-0.5" />
                <span>
                  <strong>Accounting Standard:</strong> Direct Beneficiary Transfer (DBT) is credited directly by the central government into customer bank accounts. AARKA invoices the total EPC turnkey price, keeping company revenue strictly distinct from customer subsidies.
                </span>
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
              <h2 className="text-base font-bold text-stone-900">National & State Solar Schemes Catalogue</h2>
              <p className="text-xs text-stone-500">
                Explore verified subsidy programs with official gazette rules, eligibility limits, and required documents
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-stone-500">Filter Category:</span>
              <select
                value={schemeCategoryFilter}
                onChange={(e) => setSchemeCategoryFilter(e.target.value)}
                className={`${inputClass} w-auto`}
              >
                <option value="ALL">All Scheme Categories</option>
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
                    className="flex flex-col rounded-3xl border border-stone-200/90 bg-white p-6 shadow-xs hover:shadow-lg transition duration-200 group"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-lg bg-stone-100 text-stone-700">
                        {sch.category} · {sch.jurisdiction}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2.5 py-1 rounded-full ${
                          isVerified ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {isVerified ? '✓ Verified' : 'Requires Confirmation'}
                      </span>
                    </div>

                    <h3 className="mt-3.5 text-base font-bold text-stone-950 font-display group-hover:text-emerald-800 transition">
                      {sch.name}
                    </h3>
                    <p className="mt-1 text-xs text-stone-500 line-clamp-3 leading-relaxed">
                      {sch.description}
                    </p>

                    {/* Metric Cards inside card */}
                    <div className="mt-5 rounded-2xl bg-stone-50/80 p-3.5 space-y-2 text-xs border border-stone-100">
                      <div className="flex justify-between items-center">
                        <span className="text-stone-500">Government Authority:</span>
                        <span className="font-semibold text-stone-800 text-right truncate max-w-[170px]">
                          {sch.authority}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-stone-500">Maximum Grant:</span>
                        <span className="font-black text-emerald-800">
                          {rule?.maximum_assistance ? formatCurrency(rule.maximum_assistance) : 'Tariff PPA / GBI'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-stone-500">Last Verified:</span>
                        <span className="text-stone-600 font-medium">{formatDate(sch.last_verified_at)}</span>
                      </div>
                    </div>

                    <div className="mt-auto pt-5 flex items-center justify-between border-t border-stone-100">
                      <a
                        href={sch.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs font-bold text-emerald-800 hover:text-emerald-950 flex items-center gap-1 transition"
                      >
                        Official Portal <ExternalLink className="h-3 w-3" />
                      </a>
                      <button
                        onClick={() => openSchemeModal(sch)}
                        className="text-xs font-bold text-stone-700 bg-stone-100 hover:bg-stone-200 px-3.5 py-1.5 rounded-xl transition"
                      >
                        Checklist & Rules
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
          <div className="text-center max-w-xl mx-auto">
            <h2 className="text-xl font-extrabold text-stone-900 font-display">Solar Subsidy Eligibility Checker</h2>
            <p className="mt-1 text-xs text-stone-500">
              Complete the 4-step assessment to determine qualification under official PM Surya Ghar and PM-KUSUM scheme guidelines.
            </p>
          </div>

          {/* Stepper Bar */}
          <div className="flex items-center justify-between border-b border-stone-200 pb-4 px-2">
            {[
              { num: 1, label: 'Applicant Details' },
              { num: 2, label: 'Electricity Meter' },
              { num: 3, label: 'Roof & Capacity' },
              { num: 4, label: 'Assessment Result' },
            ].map((s) => (
              <div
                key={s.num}
                className={`flex items-center gap-2 cursor-pointer transition ${
                  wizardStep === s.num ? 'text-emerald-800 font-bold scale-105' : 'text-stone-400'
                }`}
                onClick={() => setWizardStep(s.num)}
              >
                <span
                  className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold transition ${
                    wizardStep === s.num
                      ? 'bg-emerald-800 text-white shadow-md shadow-emerald-800/20'
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

          <div className="rounded-3xl border border-stone-200/80 bg-white p-6 sm:p-8 shadow-sm">
            {/* Step 1 */}
            {wizardStep === 1 && (
              <div className="space-y-5">
                <h3 className="text-sm font-bold text-stone-900 flex items-center gap-2">
                  <Home className="h-4 w-4 text-emerald-700" />
                  Step 1: Customer Profile & Category Selection
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="sm:col-span-2">
                    <label className={labelClass}>Customer Category *</label>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      {[
                        { id: 'RESIDENTIAL', label: 'Individual Homeowner', desc: 'Rooftop up to 10 kW (PM Surya Ghar)', icon: Home },
                        { id: 'GHS_RWA', label: 'Housing Society / RWA', desc: 'Common meters up to 500 kW', icon: Building },
                        { id: 'AGRICULTURAL', label: 'Farmer / Agriculture', desc: 'Solar pumps up to 7.5 HP (KUSUM)', icon: Tractor },
                      ].map((cat) => {
                        const Icon = cat.icon;
                        const isSel = eligibilityForm.customer_category === cat.id;
                        return (
                          <button
                            key={cat.id}
                            type="button"
                            onClick={() => setEligibilityForm({ ...eligibilityForm, customer_category: cat.id })}
                            className={`p-4 rounded-2xl border text-left transition flex flex-col justify-between ${
                              isSel
                                ? 'border-emerald-600 bg-emerald-50/70 text-emerald-950 ring-2 ring-emerald-600/10'
                                : 'border-stone-200 bg-stone-50/50 hover:bg-stone-100/50 text-stone-700'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <Icon className={`h-5 w-5 ${isSel ? 'text-emerald-700' : 'text-stone-400'}`} />
                              {isSel && <Check className="h-4 w-4 text-emerald-700" />}
                            </div>
                            <div className="mt-3">
                              <span className="text-xs font-bold block">{cat.label}</span>
                              <span className="text-[11px] text-stone-500 block mt-0.5">{cat.desc}</span>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div>
                    <label className={labelClass}>State / Jurisdiction *</label>
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
                    <label className={labelClass}>District / City</label>
                    <input
                      type="text"
                      placeholder="e.g. Hyderabad / Ranga Reddy"
                      value={eligibilityForm.district}
                      onChange={(e) => setEligibilityForm({ ...eligibilityForm, district: e.target.value })}
                      className={inputClass}
                    />
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
                    <label className={labelClass}>Phone Number</label>
                    <input
                      type="tel"
                      placeholder="+91 98765 43210"
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
                    className="inline-flex items-center gap-2 rounded-xl bg-emerald-800 px-6 py-2.5 text-xs font-bold text-white hover:bg-emerald-900 shadow-md transition"
                  >
                    Continue to Meter Details <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Step 2 */}
            {wizardStep === 2 && (
              <div className="space-y-5">
                <h3 className="text-sm font-bold text-stone-900 flex items-center gap-2">
                  <Zap className="h-4 w-4 text-amber-500" />
                  Step 2: Electricity Connection & DISCOM Details
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Distribution Company (DISCOM) *</label>
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
                    <span className="text-[10px] text-stone-400 mt-1 block">
                      Found at the top of your monthly electricity bill.
                    </span>
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
                    className="inline-flex items-center gap-2 rounded-xl bg-emerald-800 px-6 py-2.5 text-xs font-bold text-white hover:bg-emerald-900 shadow-md transition"
                  >
                    Continue to Roof Details <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Step 3 */}
            {wizardStep === 3 && (
              <div className="space-y-5">
                <h3 className="text-sm font-bold text-stone-900 flex items-center gap-2">
                  <SlidersHorizontal className="h-4 w-4 text-emerald-700" />
                  Step 3: Roof Surface & Proposed Capacity
                </h3>

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
                    <span className="text-[10px] text-stone-500 mt-1 block">
                      Subsidized up to 3 kW for residential households (₹78,000 max).
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
                    <span className="text-[10px] text-stone-400 mt-1 block">
                      Approx. 80-100 sq.ft shadow-free space per 1 kW.
                    </span>
                  </div>

                  <div className="sm:col-span-2">
                    <label className={labelClass}>Roof Construction Type</label>
                    <select
                      value={eligibilityForm.roof_type}
                      onChange={(e) => setEligibilityForm({ ...eligibilityForm, roof_type: e.target.value })}
                      className={inputClass}
                    >
                      <option value="RCC Flat Concrete">RCC Flat Concrete (Terrace)</option>
                      <option value="Tin / Metal Sheet">Industrial Tin / Metal Sheet</option>
                      <option value="Sloped Tile Roof">Sloped Tile / Mangalore Roof</option>
                    </select>
                  </div>

                  <div className="sm:col-span-2 space-y-2 pt-2">
                    <label className="flex items-center gap-2.5 text-xs text-stone-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={eligibilityForm.has_roof_rights}
                        onChange={(e) => setEligibilityForm({ ...eligibilityForm, has_roof_rights: e.target.checked })}
                        className="rounded border-stone-300 text-emerald-800 focus:ring-emerald-500"
                      />
                      <span>Customer holds legal ownership or explicit roof rights consent</span>
                    </label>
                    <label className="flex items-center gap-2.5 text-xs text-stone-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={eligibilityForm.is_grid_connected}
                        onChange={(e) => setEligibilityForm({ ...eligibilityForm, is_grid_connected: e.target.checked })}
                        className="rounded border-stone-300 text-emerald-800 focus:ring-emerald-500"
                      />
                      <span>Connection is grid-interactive with active utility net-metering</span>
                    </label>
                    <label className="flex items-center gap-2.5 text-xs text-stone-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={eligibilityForm.prior_subsidy_claimed}
                        onChange={(e) => setEligibilityForm({ ...eligibilityForm, prior_subsidy_claimed: e.target.checked })}
                        className="rounded border-stone-300 text-emerald-800 focus:ring-emerald-500"
                      />
                      <span>Prior central solar subsidy already claimed against this consumer meter</span>
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
                    className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-800 px-6 py-2.5 text-xs font-bold text-white shadow-lg shadow-emerald-700/20 hover:from-emerald-700 hover:to-emerald-900 transition"
                  >
                    Evaluate Eligibility <CheckCheck className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Step 4 */}
            {wizardStep === 4 && (
              <div className="space-y-6">
                {assessing ? (
                  <div className="py-14 text-center text-stone-500">
                    <RefreshCw className="h-9 w-9 animate-spin mx-auto text-emerald-800" />
                    <p className="mt-3 text-sm font-semibold text-stone-800">Assessing against official gazette rules...</p>
                    <p className="text-xs text-stone-400 mt-1">Checking PM Surya Ghar tiers and state incentives</p>
                  </div>
                ) : assessmentResult ? (
                  <div className="space-y-6">
                    <div
                      className={`rounded-3xl p-6 sm:p-8 border ${
                        assessmentResult.is_eligible
                          ? 'bg-emerald-50/80 border-emerald-200 text-emerald-950'
                          : 'bg-red-50/80 border-red-200 text-red-950'
                      }`}
                    >
                      <div className="flex items-start gap-4">
                        {assessmentResult.is_eligible ? (
                          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-emerald-600 text-white shadow-md shadow-emerald-600/30">
                            <CheckCircle className="h-7 w-7" />
                          </div>
                        ) : (
                          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-red-600 text-white shadow-md shadow-red-600/30">
                            <XCircle className="h-7 w-7" />
                          </div>
                        )}
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider block opacity-75">
                            Preliminary Assessment
                          </span>
                          <h3 className="text-xl font-black font-display mt-0.5">
                            {assessmentResult.is_eligible ? 'Potentially Eligible for Solar Subsidy' : 'Potentially Not Eligible'}
                          </h3>
                          <p className="mt-1 text-xs opacity-90">{assessmentResult.scheme_name}</p>
                        </div>
                      </div>

                      {/* Financial metrics if eligible */}
                      {assessmentResult.is_eligible && (
                        <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-3 bg-white/90 backdrop-blur rounded-2xl p-4 text-center shadow-xs">
                          <div>
                            <span className="text-[10px] uppercase font-bold text-stone-400 block tracking-wider">Central CFA</span>
                            <span className="text-lg font-black text-emerald-800 mt-1 block">
                              {formatCurrency(assessmentResult.central_subsidy)}
                            </span>
                          </div>
                          <div>
                            <span className="text-[10px] uppercase font-bold text-stone-400 block tracking-wider">State Top-up</span>
                            <span className="text-lg font-black text-blue-700 mt-1 block">
                              {formatCurrency(assessmentResult.state_subsidy)}
                            </span>
                          </div>
                          <div>
                            <span className="text-[10px] uppercase font-bold text-stone-400 block tracking-wider">Project Cost Est.</span>
                            <span className="text-lg font-bold text-stone-800 mt-1 block">
                              {formatCurrency(assessmentResult.estimated_project_cost)}
                            </span>
                          </div>
                          <div>
                            <span className="text-[10px] uppercase font-bold text-stone-400 block tracking-wider">Net Outlay</span>
                            <span className="text-lg font-black text-stone-950 mt-1 block">
                              {formatCurrency(assessmentResult.estimated_customer_outlay)}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Explanations & Conditions */}
                    <div className="space-y-3">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-stone-500">Evaluation Findings</h4>
                      <ul className="space-y-2 text-xs text-stone-700">
                        {assessmentResult.reasons.map((r, i) => (
                          <li key={i} className="flex items-start gap-2 bg-stone-50 p-2.5 rounded-xl border border-stone-100">
                            <Check className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                            <span>{r}</span>
                          </li>
                        ))}
                      </ul>

                      <h4 className="text-xs font-bold uppercase tracking-wider text-stone-500 pt-2">Compliance Requirements</h4>
                      <ul className="space-y-1.5 text-xs text-stone-600">
                        {assessmentResult.conditions.map((c, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <span className="text-stone-300 font-bold">•</span>
                            <span>{c}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Statutory Disclaimer */}
                    <div className="rounded-2xl border border-stone-200/80 bg-stone-50 p-4 text-xs text-stone-600 flex items-start gap-3">
                      <Info className="h-4 w-4 text-stone-400 shrink-0 mt-0.5" />
                      <span className="leading-relaxed">{assessmentResult.disclaimer}</span>
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
                          className="inline-flex items-center gap-2 rounded-xl bg-emerald-800 px-5 py-2.5 text-xs font-bold text-white hover:bg-emerald-900 shadow-md transition"
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
          <div className="text-center max-w-xl mx-auto">
            <h2 className="text-xl font-extrabold text-stone-900 font-display">Interactive Solar Subsidy Calculator</h2>
            <p className="mt-1 text-xs text-stone-500">
              Calculate government central financial assistance (DBT) and net customer outlays dynamically per kW.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Left Slider / Inputs */}
            <div className="rounded-3xl border border-stone-200/80 bg-white p-6 shadow-xs space-y-5">
              <h3 className="text-xs font-bold uppercase tracking-wider text-stone-500 flex items-center gap-2">
                <Sliders className="h-4 w-4 text-emerald-700" />
                Parameters
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
                <label className={labelClass}>State / UT</label>
                <select
                  value={calcInputs.state}
                  onChange={(e) => setCalcInputs({ ...calcInputs, state: e.target.value })}
                  className={inputClass}
                >
                  <option value="Telangana">Telangana</option>
                  <option value="Uttar Pradesh">Uttar Pradesh (UPNEDA)</option>
                  <option value="Delhi">Delhi</option>
                  <option value="Ladakh">Ladakh (Special State)</option>
                  <option value="Uttarakhand">Uttarakhand (Special State)</option>
                </select>
              </div>

              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className={labelClass}>Capacity (kW):</label>
                  <span className="text-sm font-black text-emerald-800">{calcInputs.capacity_kw} kW</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max={calcInputs.category === 'GHS_RWA' ? 500 : 10}
                  step="0.5"
                  value={calcInputs.capacity_kw}
                  onChange={(e) => setCalcInputs({ ...calcInputs, capacity_kw: parseFloat(e.target.value) })}
                  className="w-full accent-emerald-800 cursor-pointer h-2 bg-stone-200 rounded-lg"
                />
                <div className="flex justify-between text-[10px] text-stone-400 mt-1 font-mono">
                  <span>1 kW</span>
                  <span>{calcInputs.category === 'GHS_RWA' ? '500 kW' : '10 kW'}</span>
                </div>

                {/* Quick select buttons */}
                <div className="mt-3 grid grid-cols-4 gap-1.5">
                  {[1, 2, 3, 5].map((k) => (
                    <button
                      key={k}
                      type="button"
                      onClick={() => setCalcInputs({ ...calcInputs, capacity_kw: k })}
                      className={`py-1 rounded-lg text-[11px] font-bold transition border ${
                        calcInputs.capacity_kw === k
                          ? 'bg-emerald-800 text-white border-emerald-800'
                          : 'bg-stone-50 text-stone-600 border-stone-200 hover:bg-stone-100'
                      }`}
                    >
                      {k} kW
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Financial Display */}
            <div className="md:col-span-2 rounded-3xl border border-stone-200/80 bg-white p-6 sm:p-8 shadow-xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-stone-100 pb-4">
                  <h3 className="text-sm font-bold text-stone-900">{calcOutput?.scheme_name || 'Calculation'}</h3>
                  <span className="text-[11px] font-bold px-3 py-1 rounded-full bg-emerald-100 text-emerald-800">
                    Max Grant Cap: {formatCurrency(calcOutput?.max_subsidy_limit)}
                  </span>
                </div>

                <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="rounded-2xl border border-emerald-200/80 bg-emerald-50/70 p-4 text-center">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800 block">Government Grant</span>
                    <span className="text-2xl font-black text-emerald-950 mt-1 block">
                      {formatCurrency(calcOutput?.total_subsidy)}
                    </span>
                    <span className="text-[10px] font-semibold text-emerald-700 mt-0.5 block">Direct Bank Credit (DBT)</span>
                  </div>

                  <div className="rounded-2xl border border-stone-200 bg-stone-50 p-4 text-center">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-stone-500 block">Benchmark Cost</span>
                    <span className="text-2xl font-black text-stone-900 mt-1 block">
                      {formatCurrency(calcOutput?.estimated_cost)}
                    </span>
                    <span className="text-[10px] text-stone-400 mt-0.5 block">~₹60,000 / kW EPC</span>
                  </div>

                  <div className="rounded-2xl border border-stone-200 bg-stone-50 p-4 text-center">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-stone-500 block">Customer Outlay</span>
                    <span className="text-2xl font-black text-stone-950 mt-1 block">
                      {formatCurrency(calcOutput?.customer_contribution)}
                    </span>
                    <span className="text-[10px] text-stone-400 mt-0.5 block">Net Investment</span>
                  </div>
                </div>

                {/* Steps */}
                <div className="mt-6 space-y-2">
                  <h4 className="text-[11px] font-bold uppercase tracking-wider text-stone-400">Step-by-Step Calculation</h4>
                  <div className="rounded-2xl border border-stone-100 bg-stone-50/60 p-4 space-y-1.5 text-xs font-mono text-stone-700">
                    {calcOutput?.calculation_steps?.map((step, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <span className="text-emerald-700 font-bold">›</span>
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <p className="mt-6 text-[11px] text-stone-400 border-t border-stone-100 pt-3">
                * Note: Illustration based on MNRE 2024 Gazette Notification No. 318/331/2023-GCRT. Actual reimbursement is made after commissioning.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ================= TAB 5: APPLICATION REGISTER ================= */}
      {activeTab === 'applications' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3">
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
                className={`${inputClass} w-52`}
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
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-800 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-900 transition shadow-sm"
            >
              <Plus className="h-4 w-4" />
              Register Application
            </button>
          </div>

          <div className="rounded-3xl border border-stone-200/80 bg-white overflow-hidden shadow-xs">
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
          <div className="text-center max-w-lg mx-auto">
            <h2 className="text-xl font-extrabold text-stone-900 font-display">Customer Subsidy Tracker</h2>
            <p className="mt-1 text-xs text-stone-500">
              Track the exact 12-stage milestone status of your National Portal PM Surya Ghar subsidy application.
            </p>
          </div>

          {/* Search Box */}
          <form onSubmit={handleTrackSearch} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
              <input
                type="text"
                placeholder="Enter Application Number (SUB-2026-...) or Portal Ref (PMSG-...)"
                value={trackerSearch}
                onChange={(e) => setTrackerSearch(e.target.value)}
                className={`${inputClass} pl-10 py-3 text-xs`}
                required
              />
            </div>
            <button
              type="submit"
              disabled={trackingLoading}
              className="rounded-xl bg-emerald-800 px-6 py-3 text-xs font-bold text-white hover:bg-emerald-900 transition flex items-center gap-2 shadow-sm"
            >
              {trackingLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : 'Track Status'}
            </button>
          </form>

          {trackingError && (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-xs text-red-800 flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-600 shrink-0" />
              <span>{trackingError}</span>
            </div>
          )}

          {trackedApplication && (
            <div className="rounded-3xl border border-stone-200/80 bg-white p-6 sm:p-8 shadow-xs space-y-6">
              {/* Top Banner */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-stone-100 pb-6 gap-4">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-md">
                    {trackedApplication.category} · {trackedApplication.capacity_kw} kW System
                  </span>
                  <h3 className="mt-2 text-lg font-bold text-stone-900">{trackedApplication.customer_name}</h3>
                  <p className="text-xs text-stone-500">
                    DISCOM: {trackedApplication.discom} · Ref: <span className="font-mono text-stone-800 font-semibold">{trackedApplication.portal_reference}</span>
                  </p>
                </div>

                <div className="text-left sm:text-right">
                  <span className="text-xs text-stone-400 block font-medium">Government Grant (DBT)</span>
                  <span className="text-2xl font-black text-emerald-800 font-display">
                    {formatCurrency(trackedApplication.disbursed_subsidy > 0 ? trackedApplication.disbursed_subsidy : trackedApplication.estimated_subsidy)}
                  </span>
                  <span className="text-[10px] font-bold text-stone-500 block mt-0.5">
                    Stage: <StatusBadge status={trackedApplication.official_status || trackedApplication.internal_status} />
                  </span>
                </div>
              </div>

              {/* 12-Stage Timeline */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-stone-400">Milestone Roadmap</h4>
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
                              ? 'bg-amber-500 text-white ring-4 ring-amber-100 animate-pulse'
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
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-stone-100 text-stone-600">
                              By: {stg.responsible_party}
                            </span>
                          </div>
                          <p className="text-[11px] text-stone-500 mt-0.5 leading-relaxed">{stg.description}</p>
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
        title="Register Subsidy Application"
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
              className="rounded-xl border border-stone-200 px-4 py-2 text-xs font-bold text-stone-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-xl bg-emerald-800 px-5 py-2 text-xs font-bold text-white hover:bg-emerald-900"
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
            <div className="rounded-2xl bg-stone-50 p-4 space-y-2 text-xs">
              <p className="text-stone-700 leading-relaxed">{selectedScheme.description}</p>
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-stone-200">
                <div>
                  <span className="text-stone-400 block font-medium">Authority:</span>
                  <span className="font-bold text-stone-800">{selectedScheme.authority}</span>
                </div>
                <div>
                  <span className="text-stone-400 block font-medium">Notification Ref:</span>
                  <span className="font-mono text-stone-800">{selectedScheme.notification_reference || 'N/A'}</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-stone-500 mb-2">
                Mandatory Document Checklist by Stage
              </h4>
              <div className="space-y-3">
                {schemeChecklist?.stages?.map((stg, i) => (
                  <div key={i} className="rounded-2xl border border-stone-100 bg-white p-3.5 space-y-1.5 shadow-xs">
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
                className="rounded-xl border border-stone-200 px-4 py-2 text-xs font-bold text-stone-700"
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
            <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-stone-100 pb-4 gap-2">
              <div>
                <span className="text-xs text-stone-400 font-mono">
                  National Portal Ref: {selectedApplication.portal_application_ref || 'Pending'}
                </span>
                <h3 className="text-base font-bold text-stone-900">{selectedApplication.customer_name}</h3>
                <span className="text-xs text-stone-500">
                  {selectedApplication.discom_name} · USC: {selectedApplication.consumer_number}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowOfficialUpdateModal(true)}
                  className="rounded-xl bg-blue-50 border border-blue-200 text-blue-900 px-3.5 py-1.5 text-xs font-bold hover:bg-blue-100 transition"
                >
                  Update Official Status
                </button>
              </div>
            </div>

            {/* Sub-tabs in Drawer */}
            <div className="flex items-center gap-2 border-b border-stone-200 pb-2 text-xs">
              <button
                onClick={() => setAppDrawerTab('details')}
                className={`font-bold px-3 py-1 rounded-lg transition ${appDrawerTab === 'details' ? 'bg-stone-900 text-white' : 'text-stone-500 hover:text-stone-900'}`}
              >
                Documents & Level 2 Review ({appDocuments.length})
              </button>
              <button
                onClick={() => setAppDrawerTab('history')}
                className={`font-bold px-3 py-1 rounded-lg transition ${appDrawerTab === 'history' ? 'bg-stone-900 text-white' : 'text-stone-500 hover:text-stone-900'}`}
              >
                Audit Log ({appHistory.length})
              </button>
            </div>

            {appDrawerTab === 'details' && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-stone-500">
                    Compliance Documents (Level 2 Desk)
                  </h4>
                  <button
                    onClick={() => setShowDocUploadModal(true)}
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-800 hover:text-emerald-950"
                  >
                    <Upload className="h-3.5 w-3.5" /> Upload Document
                  </button>
                </div>

                {appDocuments.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-stone-200 p-6 text-center text-xs text-stone-400">
                    No documents uploaded yet for this application.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {appDocuments.map((doc) => (
                      <div
                        key={doc.id}
                        className="flex flex-col sm:flex-row sm:items-center justify-between rounded-2xl border border-stone-100 bg-stone-50 p-3.5 gap-2"
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
                                className="px-2.5 py-1 rounded-lg bg-emerald-700 text-white text-[10px] font-bold hover:bg-emerald-800"
                              >
                                Verify
                              </button>
                              <button
                                onClick={() => handleReviewDocument(doc.id, 'REJECTED', 'Clear copy required')}
                                className="px-2.5 py-1 rounded-lg bg-red-600 text-white text-[10px] font-bold hover:bg-red-700"
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
            )}

            {appDrawerTab === 'history' && (
              <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
                {appHistory.map((h) => (
                  <div key={h.id} className="text-xs border-l-2 border-stone-200 pl-3 py-1">
                    <div className="flex justify-between text-stone-400 text-[10px]">
                      <span>{h.updated_by} ({h.actor_type})</span>
                      <span>{formatDate(h.created_at)}</span>
                    </div>
                    <span className="font-bold text-stone-800">{h.new_status}</span>
                    <p className="text-stone-500 text-[11px] mt-0.5">{h.remarks}</p>
                  </div>
                ))}
              </div>
            )}
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
                className="rounded-xl border border-stone-200 px-4 py-2 text-xs font-bold text-stone-700"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={uploading}
                className="rounded-xl bg-emerald-800 px-5 py-2 text-xs font-bold text-white hover:bg-emerald-900"
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
              <div className="grid grid-cols-2 gap-3 bg-emerald-50 p-3.5 rounded-2xl border border-emerald-100">
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
                className="rounded-xl border border-stone-200 px-4 py-2 text-xs font-bold text-stone-700"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="rounded-xl bg-blue-800 px-5 py-2 text-xs font-bold text-white hover:bg-blue-900"
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
