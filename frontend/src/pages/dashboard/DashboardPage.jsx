import React, { useState, useEffect, useRef } from 'react';
import {
  Users,
  UserCheck,
  ClipboardCheck,
  ShoppingCart,
  Zap,
  CheckCircle,
  CreditCard,
  Boxes,
  AlertTriangle,
  Headphones,
  TrendingUp,
  RefreshCw,
  ArrowUpRight,
  ShieldCheck,
  Calendar,
  Truck
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { dashboardAPI } from '../../services/api';
import { StatCard } from '../../components/common/StatCard';
import { StatusBadge } from '../../components/common/StatusBadge';
import { useAuth } from '../../context/AuthContext';
import DirectorCommandCenter from '../../components/dashboard/DirectorCommandCenter';

const PIE_COLORS = ['#2d6a4f', '#40916c', '#52b788', '#74c69d', '#d97706', '#ef4444'];
const toDateInput = (date) => {
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return localDate.toISOString().slice(0, 10);
};
const todayInput = toDateInput(new Date());
const weekAgoInput = toDateInput(new Date(Date.now() - 6 * 24 * 60 * 60 * 1000));
const DASHBOARD_PERIODS = [
  { value: 'today', label: 'Today' },
  { value: 'week', label: 'This week' },
  { value: 'month', label: 'This month' },
  { value: 'all', label: 'All time' },
  { value: 'custom', label: 'Custom' },
];

export const DashboardPage = () => {
  const { user, hasPermission } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('all');
  const [startDate, setStartDate] = useState(weekAgoInput);
  const [endDate, setEndDate] = useState(todayInput);
  const [directorRefreshSignal, setDirectorRefreshSignal] = useState(0);
  const [loadError, setLoadError] = useState('');
  const latestRequest = useRef(0);

  const fetchDashboard = async (
    selectedPeriod,
    selectedStartDate = startDate,
    selectedEndDate = endDate,
  ) => {
    const requestId = ++latestRequest.current;
    setLoading(true);
    setLoadError('');
    try {
      const res = await dashboardAPI.getSummary(
        selectedPeriod,
        selectedStartDate,
        selectedEndDate,
      );
      if (requestId === latestRequest.current) {
        setData(res.data);
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      if (requestId === latestRequest.current) {
        setLoadError('Could not update dashboard data. Please try again.');
      }
    } finally {
      if (requestId === latestRequest.current) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    fetchDashboard(period, startDate, endDate);
  }, [period, startDate, endDate]);

  if (loading && !data) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
        <RefreshCw size={32} className="animate-spin" style={{ margin: '0 auto 12px' }} />
        <p>Loading real-time solar operations data from PostgreSQL...</p>
      </div>
    );
  }

  const { metrics, financials, charts, operational } = data || {};
  const selectedPeriodIndex = DASHBOARD_PERIODS.findIndex(({ value }) => value === period);
  const dashboardTitles = {
    'Director / Super Admin': 'Executive Operations Dashboard',
    'Operations Manager': 'Operations Control Dashboard',
    'Sales Manager': 'Sales & Customer Dashboard',
    'Warehouse Manager': 'Warehouse & Inventory Dashboard',
    'Finance Manager': 'Finance & Accounts Dashboard',
    'Installation Manager': 'Solar Installation Dashboard',
    'Service Manager': 'Service & Maintenance Dashboard',
    'Sales Executive': 'Sales Executive Dashboard',
    'Site Survey Engineer': 'Site Survey Dashboard',
    'Solar Technician': 'Technician Dashboard',
    'Dispatch Staff': 'Dispatch Dashboard',
    Storekeeper: 'Store Management Dashboard',
    'Support Executive': 'Customer Support Dashboard',
  };
  const showFinance = hasPermission('payments') || hasPermission('finance');
  const isDirector = [
    'Director / Super Admin',
    'Director / Admin',
    'Director',
    'Admin',
  ].includes(user?.role);
  const refreshDashboard = () => {
    fetchDashboard(period, startDate, endDate);
    setDirectorRefreshSignal((signal) => signal + 1);
  };

  return (
    <div className="dashboard-page">
      {/* Header & Filter Controls */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: '800', fontFamily: 'var(--font-display)', letterSpacing: '-0.02em' }}>
            {dashboardTitles[user?.role] || 'AARKA Operations Dashboard'}
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Welcome back, {user?.name}. {user?.department || 'AARKA'} operations overview
            {user?.employee_id ? ` · ${user.employee_id}` : ''}
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div className="dashboard-period-switch" role="group" aria-label="Dashboard reporting period">
            <span
              className="dashboard-period-switch-indicator"
              style={{ transform: `translateX(${selectedPeriodIndex * 100}%)` }}
              aria-hidden="true"
            />
            {DASHBOARD_PERIODS.map(({ value, label }) => (
              <button
                key={value}
                type="button"
                className={`dashboard-period-option${period === value ? ' is-active' : ''}`}
                onClick={() => setPeriod(value)}
                aria-pressed={period === value}
              >
                {label}
              </button>
            ))}
          </div>

          <button className="btn btn-secondary btn-sm" onClick={refreshDashboard} title="Refresh Data" disabled={loading}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {period === 'custom' && (
        <div className="dashboard-custom-range" aria-label="Custom dashboard date range">
          <label>
            <span>From</span>
            <input
              type="date"
              value={startDate}
              max={endDate || undefined}
              onChange={(event) => setStartDate(event.target.value)}
            />
          </label>
          <label>
            <span>To</span>
            <input
              type="date"
              value={endDate}
              min={startDate || undefined}
              max={todayInput}
              onChange={(event) => setEndDate(event.target.value)}
            />
          </label>
        </div>
      )}

      {loadError && (
        <div role="alert" className="alert alert-danger" style={{ marginBottom: '16px' }}>
          {loadError}
        </div>
      )}

      {isDirector && (
        <DirectorCommandCenter
          period={period}
          startDate={startDate}
          endDate={endDate}
          refreshSignal={directorRefreshSignal}
        />
      )}

      {/* Financial Overview Banner */}
      {showFinance && <div
        className="aarka-card"
        style={{
          background: 'linear-gradient(135deg, #0c2318 0%, #174530 100%)',
          color: '#ffffff',
          padding: '24px 28px',
          marginBottom: '24px',
          boxShadow: 'var(--shadow-md)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.12)', paddingBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={20} color="#a7e4c2" />
            <span style={{ fontSize: '14px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#a7e4c2' }}>
              Project Financial Health & Recognized Margins
            </span>
          </div>
          <span style={{ fontSize: '12px', color: '#94bca7' }}>Calculated strictly from audited PostgreSQL ledger</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
          <div>
            <div style={{ fontSize: '12px', color: '#a7e4c2', fontWeight: '600', textTransform: 'uppercase' }}>Recognized Revenue</div>
            <div style={{ fontSize: '26px', fontWeight: '800', fontFamily: 'var(--font-display)', marginTop: '4px' }}>
              ₹{(financials?.total_revenue || 0).toLocaleString()}
            </div>
            <div style={{ fontSize: '11px', color: '#94bca7', marginTop: '2px' }}>Total agreed customer contracts</div>
          </div>

          <div>
            <div style={{ fontSize: '12px', color: '#a7e4c2', fontWeight: '600', textTransform: 'uppercase' }}>Cash Received</div>
            <div style={{ fontSize: '26px', fontWeight: '800', fontFamily: 'var(--font-display)', marginTop: '4px', color: '#78c59f' }}>
              ₹{(financials?.cash_received || 0).toLocaleString()}
            </div>
            <div style={{ fontSize: '11px', color: '#94bca7', marginTop: '2px' }}>Bank & UPI verified receipts</div>
          </div>

          <div>
            <div style={{ fontSize: '12px', color: '#fca5a5', fontWeight: '600', textTransform: 'uppercase' }}>Outstanding Receivables</div>
            <div style={{ fontSize: '26px', fontWeight: '800', fontFamily: 'var(--font-display)', marginTop: '4px', color: '#f87171' }}>
              ₹{(financials?.outstanding_receivables || 0).toLocaleString()}
            </div>
            <div style={{ fontSize: '11px', color: '#94bca7', marginTop: '2px' }}>Pending stage milestone payments</div>
          </div>

          <div>
            <div style={{ fontSize: '12px', color: '#fcd34d', fontWeight: '600', textTransform: 'uppercase' }}>Recorded Project Costs</div>
            <div style={{ fontSize: '26px', fontWeight: '800', fontFamily: 'var(--font-display)', marginTop: '4px', color: '#fbbf24' }}>
              ₹{(financials?.total_expenses || 0).toLocaleString()}
            </div>
            <div style={{ fontSize: '11px', color: '#94bca7', marginTop: '2px' }}>Hardware + Labour + Operations</div>
          </div>

          <div>
            <div style={{ fontSize: '12px', color: '#a7e4c2', fontWeight: '600', textTransform: 'uppercase' }}>Gross Profit Margin</div>
            <div style={{ fontSize: '26px', fontWeight: '800', fontFamily: 'var(--font-display)', marginTop: '4px', color: '#34d399' }}>
              {financials?.gross_margin_percentage || 0}%
            </div>
            <div style={{ fontSize: '11px', color: '#94bca7', marginTop: '2px' }}>₹{(financials?.gross_margin || 0).toLocaleString()} net contribution</div>
          </div>
        </div>
      </div>}

      {/* 12 Core Business Operational Metrics */}
      <div className="stat-grid">
        {hasPermission('customers') && <StatCard title="Total Customers" value={metrics?.total_customers || 0} icon={UserCheck} subtext="Residential & Commercial accounts" />}
        {hasPermission('leads') && <>
          <StatCard title="Total Inquiries" value={metrics?.total_enquiries || 0} icon={Users} subtext={`${metrics?.new_leads || 0} new leads pending contact`} />
          <StatCard title="Qualified Leads" value={metrics?.qualified_leads || 0} icon={CheckCircle} color="accent" subtext="Ready for site inspection" />
        </>}
        {hasPermission('surveys') && <StatCard title="Pending Site Surveys" value={metrics?.pending_site_surveys || 0} icon={ClipboardCheck} color="accent" subtext="Awaiting technician visit" />}
        {hasPermission('quotations') && <StatCard title="Approved Quotations" value={metrics?.approved_quotations || 0} icon={ShoppingCart} subtext="Quotations agreed by customer" />}
        {hasPermission('orders') && <StatCard title="Confirmed Orders" value={metrics?.confirmed_orders || 0} icon={ShoppingCart} subtext="Active project lifecycle orders" />}
        {hasPermission('installations') && <>
          <StatCard title="Active Installations" value={metrics?.active_installations || 0} icon={Zap} color="accent" subtext="Field crews currently deployed" />
          <StatCard title="Completed Projects" value={metrics?.completed_installations || 0} icon={CheckCircle} subtext="Signed customer acceptance" />
        </>}
        {hasPermission('inventory') && <>
          {showFinance && <StatCard title="Inventory Valuation" value={`₹${(metrics?.inventory_valuation || 0).toLocaleString()}`} icon={Boxes} subtext="Current warehouse asset balance" />}
          <StatCard title="Low-Stock Alerts" value={metrics?.low_stock_count || 0} icon={AlertTriangle} color="accent" subtext="Below configured reorder levels" />
        </>}
        {hasPermission('service') && <StatCard title="Open Service Tickets" value={metrics?.open_service_tickets || 0} icon={Headphones} subtext="After-sales maintenance & repairs" />}
        {hasPermission('warranties') && <StatCard title="Active Warranties" value={metrics?.active_warranties || 0} icon={ShieldCheck} subtext="Equipment under active coverage" />}
      </div>

      {/* Analytical Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', marginBottom: '24px' }}>
        {/* Monthly Revenue & Installation Trend */}
        {showFinance && <div className="aarka-card">
          <div className="aarka-card-header">
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '700' }}>Revenue & Installation Activity</h3>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Orders and installations created during {DASHBOARD_PERIODS.find((option) => option.value === period)?.label.toLowerCase()}.
              </p>
            </div>
          </div>
          <div className="aarka-card-body" style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts?.revenue_trend || []} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <XAxis dataKey="month" stroke="var(--text-light)" fontSize={12} />
                <YAxis yAxisId="left" stroke="var(--color-primary-600)" fontSize={12} tickFormatter={(val) => `₹${val / 1000}k`} />
                <YAxis yAxisId="right" orientation="right" stroke="var(--color-amber-500)" fontSize={12} />
                <Tooltip
                  formatter={(val, name) => [name === 'revenue' ? `₹${val.toLocaleString()}` : val, name === 'revenue' ? 'Revenue' : 'Installations']}
                  contentStyle={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Bar yAxisId="left" dataKey="revenue" name="Revenue (₹)" fill="#2d6a4f" radius={[4, 4, 0, 0]} />
                <Line yAxisId="right" type="monotone" dataKey="installations" name="Installations Count" stroke="#f59e0b" strokeWidth={3} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>}

        {/* Project Status Pie Chart */}
        {hasPermission('orders') && <div className="aarka-card">
          <div className="aarka-card-header">
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '700' }}>Project Status Distribution</h3>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Active orders across lifecycle stages</p>
            </div>
          </div>
          <div className="aarka-card-body" style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={charts?.project_status_dist || []}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={95}
                  paddingAngle={4}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {(charts?.project_status_dist || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val, name) => [val, name]}
                  contentStyle={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>}
      </div>

      {/* Conversion Funnel & Operational Tables */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
        {/* Sales Conversion Funnel */}
        {hasPermission('leads') && <div className="aarka-card">
          <div className="aarka-card-header">
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '700' }}>End-to-End Sales Conversion Funnel</h3>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>From inquiry receipt to customer handover</p>
            </div>
          </div>
          <div className="aarka-card-body">
            {(charts?.funnel || []).map((step, idx) => {
              const maxCount = charts?.funnel[0]?.count || 1;
              const pct = Math.max(8, Math.round((step.count / maxCount) * 100));
              return (
                <div key={idx} style={{ marginBottom: '14px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: '600', marginBottom: '4px' }}>
                    <span>{step.stage}</span>
                    <span style={{ color: 'var(--color-primary-700)' }}>{step.count} ({pct}%)</span>
                  </div>
                  <div style={{ height: '10px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px', overflow: 'hidden' }}>
                    <div
                      style={{
                        height: '100%',
                        width: `${pct}%`,
                        backgroundColor: idx === 0 ? '#1b4d36' : (idx === 4 ? '#2e8b60' : '#48a679'),
                        borderRadius: '6px',
                        transition: 'width 0.5s ease',
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>}

        {/* Recent Inquiries List */}
        {hasPermission('leads') && <div className="aarka-card">
          <div className="aarka-card-header">
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '700' }}>Latest Customer Inquiries</h3>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Recently received rooftop solar leads</p>
            </div>
            <a href="/leads" className="btn btn-secondary btn-sm">View All Leads →</a>
          </div>
          <div className="aarka-card-body" style={{ padding: '0' }}>
            <table className="aarka-table">
              <thead>
                <tr>
                  <th>Lead Ref</th>
                  <th>Customer</th>
                  <th>Capacity</th>
                  <th>Stage</th>
                </tr>
              </thead>
              <tbody>
                {(operational?.recent_leads || []).map((lead) => (
                  <tr key={lead.id}>
                    <td>
                      <span style={{ fontWeight: '700', color: 'var(--color-primary-800)' }}>
                        {lead.ref}
                      </span>
                    </td>
                    <td>
                      <div style={{ fontWeight: '600' }}>{lead.name}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{lead.phone}</div>
                    </td>
                    <td>{lead.capacity} kW</td>
                    <td><StatusBadge status={lead.stage} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>}
      </div>

      {/* Today's Operational Dispatches & Installations */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Field Assignments */}
        {hasPermission('installations') && <div className="aarka-card">
          <div className="aarka-card-header">
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '700' }}>Today's Scheduled Installations</h3>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Assigned field technician deployment</p>
            </div>
            <a href="/installations" className="btn btn-secondary btn-sm">Field Ops →</a>
          </div>
          <div className="aarka-card-body" style={{ padding: '0' }}>
            <table className="aarka-table">
              <thead>
                <tr>
                  <th>Job Number</th>
                  <th>Customer</th>
                  <th>Technician</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {(operational?.today_installations || []).length === 0 ? (
                  <tr>
                    <td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-light)', padding: '24px' }}>
                      No installations scheduled for today
                    </td>
                  </tr>
                ) : (
                  (operational?.today_installations || []).map((inst) => (
                    <tr key={inst.id}>
                      <td><span style={{ fontWeight: '700' }}>{inst.job_number}</span></td>
                      <td>{inst.customer}</td>
                      <td><span style={{ color: 'var(--color-primary-700)', fontWeight: '600' }}>{inst.tech}</span></td>
                      <td><StatusBadge status={inst.status} /></td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>}

        {/* Low Stock Alerts */}
        {hasPermission('inventory') && <div className="aarka-card">
          <div className="aarka-card-header">
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '700' }}>Warehouse Inventory Alerts</h3>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Products nearing or below minimum reorder thresholds</p>
            </div>
            <a href="/inventory" className="btn btn-secondary btn-sm">Inventory →</a>
          </div>
          <div className="aarka-card-body" style={{ padding: '0' }}>
            <table className="aarka-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>SKU</th>
                  <th>In Stock</th>
                  <th>Reorder Level</th>
                </tr>
              </thead>
              <tbody>
                {(operational?.low_stock_items || []).length === 0 ? (
                  <tr>
                    <td colSpan={4} style={{ textAlign: 'center', color: 'var(--color-primary-600)', padding: '24px', fontWeight: '600' }}>
                      ✓ All products are comfortably stocked above reorder levels
                    </td>
                  </tr>
                ) : (
                  (operational?.low_stock_items || []).map((item) => (
                    <tr key={item.id}>
                      <td style={{ fontWeight: '600' }}>{item.name}</td>
                      <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{item.sku}</td>
                      <td>
                        <span style={{ fontWeight: '700', color: 'var(--color-rose-600)' }}>
                          {item.qty} units
                        </span>
                      </td>
                      <td>{item.min} units</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>}
      </div>
    </div>
  );

};



export default DashboardPage;
