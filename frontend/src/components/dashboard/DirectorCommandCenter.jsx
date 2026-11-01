import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowUpRight,
  Banknote,
  Boxes,
  BriefcaseBusiness,
  Building2,
  CheckCircle2,
  ClipboardList,
  FileWarning,
  RefreshCw,
  Wrench,
} from 'lucide-react';
import { dashboardAPI } from '../../services/api';

const currency = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
});

const formatMoney = (value) => (
  value === null || value === undefined ? 'Data unavailable' : currency.format(value)
);

const KPI_CARDS = [
  {
    key: 'recognized_revenue',
    title: 'Recognized revenue',
    description: 'Completed orders in selected period',
    icon: Banknote,
    tone: 'green',
    href: '/finance',
    comparison: 'revenue_change_percentage',
  },
  {
    key: 'net_profit',
    title: 'Net profit',
    description: 'Recorded costs against completed work',
    icon: CheckCircle2,
    tone: 'green',
    href: '/finance',
    comparison: 'profit_change_percentage',
  },
  {
    key: 'cash_received',
    title: 'Cash collected',
    description: 'Verified receipts in selected period',
    icon: Building2,
    tone: 'blue',
    href: '/payments',
    comparison: 'cash_change_percentage',
  },
  {
    key: 'outstanding_receivables',
    title: 'Outstanding',
    description: 'Current balances; historical snapshots unavailable',
    icon: FileWarning,
    tone: 'amber',
    href: '/payments',
  },
  {
    key: 'recorded_expenses',
    title: 'Recorded expenses',
    description: 'Direct costs and recorded operating spend',
    icon: BriefcaseBusiness,
    tone: 'amber',
    href: '/finance',
    comparison: 'expenses_change_percentage',
  },
  {
    key: 'advance_payments',
    title: 'Customer advances',
    description: 'Current recorded advances; separate from selected-period receipts',
    icon: Banknote,
    tone: 'blue',
    href: '/payments',
  },
  {
    key: 'inventory_value',
    title: 'Inventory value',
    description: 'Current stock; historical snapshots unavailable',
    icon: Boxes,
    tone: 'blue',
    href: '/inventory',
    source: 'operations',
  },
];

const OPERATION_LINKS = [
  { key: 'unfinished_installations', label: 'Unfinished projects', href: '/installations', icon: ClipboardList },
  { key: 'delayed_installations', label: 'Delayed installations', href: '/installations', icon: AlertTriangle },
  { key: 'open_service_tickets', label: 'Open service tickets', href: '/service', icon: Wrench },
  { key: 'pending_subsidies', label: 'Subsidies needing attention', href: '/subsidies', icon: Building2 },
  { key: 'overdue_invoices', label: 'Overdue invoices', href: '/payments', icon: FileWarning },
];

export default function DirectorCommandCenter({
  period,
  startDate,
  endDate,
  refreshSignal,
}) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reloadKey, setReloadKey] = useState(0);
  const [projectSearch, setProjectSearch] = useState('');
  const [expandedProjectId, setExpandedProjectId] = useState(null);

  useEffect(() => {
    let active = true;
    const loadSummary = async () => {
      setLoading(true);
      setError('');
      try {
        const response = await dashboardAPI.getDirectorSummary(period, startDate, endDate);
        if (active) setSummary(response.data);
      } catch (requestError) {
        console.error('Failed to load director command center:', requestError);
        if (active) setError('The director overview could not be loaded. Please retry.');
      } finally {
        if (active) setLoading(false);
      }
    };
    loadSummary();
    return () => {
      active = false;
    };
  }, [period, startDate, endDate, reloadKey, refreshSignal]);

  const projectRows = useMemo(() => {
    const query = projectSearch.trim().toLowerCase();
    return (summary?.projects || []).filter((project) => (
      !query
      || project.reference.toLowerCase().includes(query)
      || project.customer.toLowerCase().includes(query)
    ));
  }, [summary, projectSearch]);
  const financials = summary?.financials || {};
  const operations = summary?.operations || {};
  const generatedAt = summary?.generated_at
    ? new Date(summary.generated_at).toLocaleString('en-IN', {
      dateStyle: 'medium',
      timeStyle: 'short',
    })
    : null;

  return (
    <section className="director-command-center" aria-labelledby="director-command-title">
      <header className="director-command-header">
        <div>
          <div className="director-eyebrow">EXECUTIVE OVERVIEW</div>
          <h2 id="director-command-title">Director&apos;s Command Center</h2>
          <p>Company-wide financial health, project delivery and actions that need attention.</p>
        </div>
        <div className="director-header-meta">
          <span className="director-live-indicator"><i /> Live records</span>
          {generatedAt && <span>Updated {generatedAt}</span>}
          <Link className="director-report-link" to="/reports">
            Reports & exports <ArrowUpRight size={13} />
          </Link>
        </div>
      </header>

      {error && (
        <div className="director-error" role="alert">
          <span>{error}</span>
          <button type="button" onClick={() => setReloadKey((key) => key + 1)}>Retry</button>
        </div>
      )}

      {loading && !summary ? (
        <div className="director-loading" role="status">
          <RefreshCw size={18} className="animate-spin" /> Loading company records…
        </div>
      ) : summary && (
        <>
          <div className="director-kpi-grid">
            {KPI_CARDS.map((card) => {
              const Icon = card.icon;
              const source = card.source === 'operations' ? operations : financials;
              const amount = source[card.key];
              const comparison = card.comparison
                ? financials[card.comparison]
                : null;
              const comparisonIsNegative = card.key === 'recorded_expenses'
                ? comparison > 0
                : comparison < 0;
              return (
                <Link
                  className={`director-kpi-card tone-${card.tone}${card.key === 'net_profit' && amount < 0 ? ' is-negative' : ''}`}
                  to={card.href}
                  key={card.key}
                >
                  <div className="director-kpi-heading">
                    <span>{card.title}</span>
                    <Icon size={18} aria-hidden="true" />
                  </div>
                  <strong>{formatMoney(amount)}</strong>
                  {comparison !== null && comparison !== undefined && (
                    <span className={`director-comparison${comparisonIsNegative ? ' is-negative' : ''}`}>
                      {comparison > 0 ? '+' : ''}
                      {comparison}% vs previous period
                    </span>
                  )}
                  <small>{card.description}</small>
                  <ArrowUpRight size={14} className="director-kpi-link-icon" aria-hidden="true" />
                </Link>
              );
            })}
          </div>

          <div className="director-command-grid">
            <section className="director-panel director-project-panel">
              <div className="director-panel-heading">
                <div>
                  <h3>Installation profitability</h3>
                  <p>Recent project records. Open finance for the full register; missing costs are flagged.</p>
                </div>
                <div className="director-project-actions">
                  <input
                    type="search"
                    aria-label="Search projects"
                    placeholder="Search projects"
                    value={projectSearch}
                    onChange={(event) => setProjectSearch(event.target.value)}
                  />
                  <Link to="/finance">Open finance <ArrowUpRight size={14} /></Link>
                </div>
              </div>
              <div className="director-table-wrap">
                <table className="director-project-table">
                  <thead>
                    <tr>
                      <th>Project</th>
                      <th>Customer / system</th>
                      <th>Status</th>
                      <th>Contract</th>
                      <th>Recorded cost</th>
                      <th>Contribution</th>
                    </tr>
                  </thead>
                  <tbody>
                    {projectRows.length ? projectRows.map((project) => (
                      <React.Fragment key={project.id}>
                        <tr>
                          <td>
                            <button
                              className="director-project-reference"
                              type="button"
                              aria-expanded={expandedProjectId === project.id}
                              aria-controls={`project-details-${project.id}`}
                              onClick={() => setExpandedProjectId(
                                (current) => current === project.id ? null : project.id
                              )}
                            >
                              {project.reference}
                            </button>
                          </td>
                          <td>
                            <strong>{project.customer}</strong>
                            <small>{project.capacity_kw ?? '—'} kW</small>
                          </td>
                          <td>
                            <span className="director-status-pill">{(project.installation_status || project.status || 'Pending').replaceAll('_', ' ')}</span>
                          </td>
                          <td>{formatMoney(project.contract_value)}</td>
                          <td>{project.cost_data_available ? formatMoney(project.recorded_cost) : 'Pending data'}</td>
                          <td className={
                            !project.cost_data_available
                              ? 'director-amount-missing'
                              : project.contribution < 0
                                ? 'director-amount-negative'
                                : 'director-amount-positive'
                          }>
                            {project.cost_data_available ? formatMoney(project.contribution) : 'Incomplete'}
                          </td>
                        </tr>
                        {expandedProjectId === project.id && (
                          <tr className="director-project-detail-row">
                            <td colSpan={6} id={`project-details-${project.id}`}>
                              <div className="director-project-breakdown">
                                <span><small>Hardware</small><strong>{formatMoney(project.cost_breakdown.panels_and_hardware)}</strong></span>
                                <span><small>Installation labour</small><strong>{formatMoney(project.cost_breakdown.installation_labour)}</strong></span>
                                <span><small>Transportation</small><strong>{formatMoney(project.cost_breakdown.transportation)}</strong></span>
                                <span><small>Other recorded</small><strong>{formatMoney(project.cost_breakdown.other_recorded_expenses)}</strong></span>
                                <span><small>Advance received</small><strong>{formatMoney(project.advance_paid)}</strong></span>
                                <span><small>Balance due</small><strong>{formatMoney(project.balance_due)}</strong></span>
                                <span><small>Margin</small><strong>{project.margin_percentage === null ? 'Data unavailable' : `${project.margin_percentage}%`}</strong></span>
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    )) : (
                      <tr><td colSpan={6} className="director-empty">No project records for this reporting period.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <aside className="director-side-stack">
              <section className="director-panel">
                <div className="director-panel-heading">
                  <div>
                    <h3>Operating pulse</h3>
                    <p>Current work across teams</p>
                  </div>
                </div>
                <div className="director-operation-list">
                  {OPERATION_LINKS.map((item) => {
                    const Icon = item.icon;
                    return (
                      <Link to={item.href} key={item.key}>
                        <span className="director-operation-icon"><Icon size={16} /></span>
                        <span>{item.label}</span>
                        <strong>{operations[item.key] ?? '—'}</strong>
                        <ArrowUpRight size={13} />
                      </Link>
                    );
                  })}
                  <div className="director-unavailable">
                    <span>Technician payments</span>
                    <strong>{formatMoney(financials.pending_technician_payments)}</strong>
                  </div>
                  <div className="director-unavailable">
                    <span>Supplier payables</span>
                    <strong>{formatMoney(financials.pending_supplier_payables)}</strong>
                  </div>
                </div>
              </section>

              <section className="director-panel director-alert-panel">
                <div className="director-panel-heading">
                  <div>
                    <h3><AlertTriangle size={17} /> Priority alerts</h3>
                    <p>Generated from live records</p>
                  </div>
                </div>
                {summary.alerts.length ? (
                  <div className="director-alert-list">
                    {summary.alerts.slice(0, 5).map((alert, index) => (
                      <Link to={alert.href} className={`director-alert severity-${alert.severity}`} key={`${alert.title}-${index}`}>
                        <span>{alert.title}</span>
                        <small>{alert.description}</small>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <div className="director-empty director-empty-alert">No active alerts in the records checked.</div>
                )}
              </section>
            </aside>
          </div>

          <div className="director-data-note">
            <strong>Data coverage</strong>
            <span>
              Some requested figures are not tracked yet. Technician payroll and supplier payable
              balances are shown as unavailable rather than estimated. Profitability is based on
              recorded costs; projects with incomplete cost data are marked.
            </span>
          </div>
        </>
      )}
    </section>
  );
}
