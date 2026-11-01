import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, DollarSign, PieChart, Receipt, Plus, 
  ArrowUpRight, ArrowDownRight, FileSpreadsheet, Download 
} from 'lucide-react';
import { financeApi } from '../../services/api';
import StatCard from '../../components/common/StatCard';
import DataTable from '../../components/common/DataTable';
import Modal from '../../components/common/Modal';

export default function FinancePage() {
  const [profitability, setProfitability] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('PROFITABILITY'); // PROFITABILITY | EXPENSES | INVOICES

  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [expenseForm, setExpenseForm] = useState({
    order_id: '',
    category: 'MATERIAL',
    amount: '',
    description: '',
    vendor_name: '',
    invoice_reference: ''
  });
  const [feedback, setFeedback] = useState(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [pRes, eRes, iRes] = await Promise.all([
        financeApi.getProfitability(),
        financeApi.getExpenses(),
        financeApi.getInvoices()
      ]);
      setProfitability(pRes.data);
      setExpenses(eRes.data);
      setInvoices(iRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRecordExpense = async (e) => {
    e.preventDefault();
    try {
      await financeApi.recordExpense({
        ...expenseForm,
        order_id: expenseForm.order_id ? parseInt(expenseForm.order_id) : null,
        amount: parseFloat(expenseForm.amount)
      });
      setFeedback({ type: 'success', msg: 'Expense recorded successfully against project ledger.' });
      setShowExpenseModal(false);
      setExpenseForm({
        order_id: '',
        category: 'MATERIAL',
        amount: '',
        description: '',
        vendor_name: '',
        invoice_reference: ''
      });
      fetchData();
    } catch (err) {
      setFeedback({ type: 'error', msg: err.response?.data?.detail || 'Failed to record expense' });
    }
  };

  // Calculations
  const totalRevenue = profitability.reduce((sum, p) => sum + (p.order_value || 0), 0);
  const totalCost = profitability.reduce((sum, p) => sum + (p.total_cost || 0), 0);
  const totalGrossProfit = totalRevenue - totalCost;
  const avgMargin = totalRevenue > 0 ? ((totalGrossProfit / totalRevenue) * 100).toFixed(1) : 0;

  const profitabilityColumns = [
    {
      header: 'Sales Order #',
      accessor: 'order_number',
      cell: (row) => (
        <span className="font-semibold text-emerald-800 font-mono text-sm">
          {row.order_number}
        </span>
      )
    },
    {
      header: 'Customer',
      accessor: 'customer_name',
      cell: (row) => <span className="font-medium text-stone-900">{row.customer_name}</span>
    },
    {
      header: 'Recognized Revenue',
      accessor: 'order_value',
      cell: (row) => (
        <span className="font-semibold text-stone-900">
          ₹{row.order_value?.toLocaleString('en-IN')}
        </span>
      )
    },
    {
      header: 'Material BOM Cost',
      accessor: 'material_cost',
      cell: (row) => (
        <span className="text-stone-600 text-sm">
          ₹{row.material_cost?.toLocaleString('en-IN')}
        </span>
      )
    },
    {
      header: 'Labor Cost',
      accessor: 'technician_cost',
      cell: (row) => (
        <span className="text-stone-600 text-sm">
          ₹{row.technician_cost?.toLocaleString('en-IN')}
        </span>
      )
    },
    {
      header: 'Total Cost',
      accessor: 'total_cost',
      cell: (row) => (
        <span className="font-medium text-stone-700">
          ₹{row.total_cost?.toLocaleString('en-IN')}
        </span>
      )
    },
    {
      header: 'Gross Profit (Rule #15)',
      accessor: 'gross_profit',
      cell: (row) => (
        <div className="flex items-center gap-1 font-semibold text-emerald-700">
          <ArrowUpRight className="w-4 h-4 text-emerald-600" />
          ₹{row.gross_profit?.toLocaleString('en-IN')}
        </div>
      )
    },
    {
      header: 'Margin %',
      accessor: 'gross_margin_percentage',
      cell: (row) => (
        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
          row.gross_margin_percentage >= 25 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
        }`}>
          {row.gross_margin_percentage?.toFixed(1)}%
        </span>
      )
    }
  ];

  const expenseColumns = [
    {
      header: 'Expense Date',
      accessor: 'created_at',
      cell: (row) => (
        <span className="text-xs text-stone-600 font-mono">
          {new Date(row.created_at).toLocaleDateString()}
        </span>
      )
    },
    {
      header: 'Order Ref',
      accessor: 'order_id',
      cell: (row) => (
        <span className="font-mono text-xs text-emerald-800">
          {row.order_id ? `ORD-#${row.order_id}` : 'General Overhead'}
        </span>
      )
    },
    {
      header: 'Category',
      accessor: 'category',
      cell: (row) => (
        <span className="text-xs px-2 py-0.5 rounded bg-stone-100 text-stone-700 font-medium">
          {row.category}
        </span>
      )
    },
    {
      header: 'Description & Vendor',
      accessor: 'description',
      cell: (row) => (
        <div>
          <div className="text-sm font-medium text-stone-800">{row.description}</div>
          <div className="text-xs text-stone-500">Vendor: {row.vendor_name || 'N/A'} • Inv: {row.invoice_reference || 'N/A'}</div>
        </div>
      )
    },
    {
      header: 'Amount',
      accessor: 'amount',
      cell: (row) => (
        <span className="font-semibold text-stone-900">
          ₹{row.amount?.toLocaleString('en-IN')}
        </span>
      )
    }
  ];

  const invoiceColumns = [
    {
      header: 'Invoice #',
      accessor: 'invoice_number',
      cell: (row) => <span className="font-mono font-semibold text-emerald-800">{row.invoice_number}</span>
    },
    {
      header: 'Customer',
      accessor: 'customer_name',
      cell: (row) => <span className="font-medium text-stone-800">{row.customer_name}</span>
    },
    {
      header: 'Taxable Amount',
      accessor: 'subtotal',
      cell: (row) => <span>₹{row.subtotal?.toLocaleString('en-IN')}</span>
    },
    {
      header: 'GST (13.8%)',
      accessor: 'gst_amount',
      cell: (row) => <span className="text-xs text-stone-600">₹{row.gst_amount?.toLocaleString('en-IN')}</span>
    },
    {
      header: 'Total Payable',
      accessor: 'total_amount',
      cell: (row) => <span className="font-bold text-stone-900">₹{row.total_amount?.toLocaleString('en-IN')}</span>
    },
    {
      header: 'Payment Status',
      accessor: 'status',
      cell: (row) => (
        <span className={`text-xs px-2 py-0.5 rounded font-medium ${
          row.status === 'PAID' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
        }`}>
          {row.status}
        </span>
      )
    }
  ];

  return (
    <div className="space-y-6 enterprise-page enterprise-finance-page">
      {/* Header */}
      <div className="enterprise-page-header">
        <div className="enterprise-page-copy">
          <span className="enterprise-eyebrow">Finance · Project economics</span>
          <h1 className="text-2xl font-bold text-stone-900 tracking-tight">Financial & Project Profitability Ledger</h1>
          <p className="text-sm text-stone-600 mt-1">
            Real-time project gross margin calculations, expense tracking against BOM, and tax invoice generation.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowExpenseModal(true)}
            className="btn btn-glass"
          >
            <Plus className="w-4 h-4" />
            Record Expense
          </button>
        </div>
      </div>

      {feedback && (
        <div className={`p-4 rounded-lg flex items-center justify-between text-sm ${
          feedback.type === 'success' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-rose-50 text-rose-800 border border-rose-200'
        }`}>
          <span>{feedback.msg}</span>
          <button onClick={() => setFeedback(null)} className="text-xs underline font-medium">Dismiss</button>
        </div>
      )}

      {/* KPI Stats */}
      <div className="enterprise-kpi-grid grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Project Revenue"
          value={`₹${totalRevenue.toLocaleString('en-IN')}`}
          icon={TrendingUp}
          subtext="Cumulative recognized revenue"
        />
        <StatCard
          title="Total Project Costs"
          value={`₹${totalCost.toLocaleString('en-IN')}`}
          icon={PieChart}
          subtext="BOM + Labor + Overheads"
        />
        <StatCard
          title="Gross Margin (Rule #15)"
          value={`₹${totalGrossProfit.toLocaleString('en-IN')}`}
          icon={DollarSign}
          subtext={`Average Margin: ${avgMargin}%`}
        />
        <StatCard
          title="GST Invoices"
          value={invoices.length}
          icon={Receipt}
          subtext="Generated commercial invoices"
        />
      </div>

      {/* Tabs */}
      <div className="enterprise-section-tabs" role="tablist" aria-label="Finance sections">
        <button
          onClick={() => setActiveTab('PROFITABILITY')}
          className={`enterprise-section-tab${activeTab === 'PROFITABILITY' ? ' is-active' : ''}`}
          role="tab"
          aria-selected={activeTab === 'PROFITABILITY'}
        >
          Project Profitability (Rule #15)
        </button>
        <button
          onClick={() => setActiveTab('EXPENSES')}
          className={`enterprise-section-tab${activeTab === 'EXPENSES' ? ' is-active' : ''}`}
          role="tab"
          aria-selected={activeTab === 'EXPENSES'}
        >
          Recorded Expenses ({expenses.length})
        </button>
        <button
          onClick={() => setActiveTab('INVOICES')}
          className={`enterprise-section-tab${activeTab === 'INVOICES' ? ' is-active' : ''}`}
          role="tab"
          aria-selected={activeTab === 'INVOICES'}
        >
          Tax Invoices ({invoices.length})
        </button>
      </div>

      {/* Active Tab Content */}
      {activeTab === 'PROFITABILITY' && (
        <DataTable
          className="enterprise-table-card"
          title="Project profitability"
          subtitle="Revenue, costs, and gross margin by project"
          columns={profitabilityColumns}
          data={profitability}
          loading={loading}
          emptyMessage="No completed or active orders with cost tracking yet."
        />
      )}

      {activeTab === 'EXPENSES' && (
        <DataTable
          className="enterprise-table-card"
          title="Project expenses"
          subtitle="Recorded project costs and general overhead"
          columns={expenseColumns}
          data={expenses}
          loading={loading}
          emptyMessage="No project expenses logged yet."
        />
      )}

      {activeTab === 'INVOICES' && (
        <DataTable
          className="enterprise-table-card"
          title="Tax invoices"
          subtitle="Customer billing and payment status"
          columns={invoiceColumns}
          data={invoices}
          loading={loading}
          emptyMessage="No invoices generated yet."
        />
      )}

      {/* Record Expense Modal */}
      <Modal
        isOpen={showExpenseModal}
        onClose={() => setShowExpenseModal(false)}
        title="Record Project / Operational Expense"
      >
        <form onSubmit={handleRecordExpense} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Sales Order ID (Optional)</label>
            <input
              type="number"
              placeholder="e.g. 1 (Leave blank for general overhead)"
              value={expenseForm.order_id}
              onChange={(e) => setExpenseForm({ ...expenseForm, order_id: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Expense Category *</label>
              <select
                value={expenseForm.category}
                onChange={(e) => setExpenseForm({ ...expenseForm, category: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none bg-white"
              >
                <option value="MATERIAL">Material Purchase</option>
                <option value="LABOR">Technician / Subcontractor Labor</option>
                <option value="LOGISTICS">Transport & Freight</option>
                <option value="PERMIT">DISCOM Net Metering & Inspection</option>
                <option value="OVERHEAD">General Operations</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Amount (₹) *</label>
              <input
                type="number"
                step="0.01"
                required
                placeholder="e.g. 15000"
                value={expenseForm.amount}
                onChange={(e) => setExpenseForm({ ...expenseForm, amount: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Description *</label>
            <input
              type="text"
              required
              placeholder="e.g. Crane rental for high-rise rooftop inverter lift"
              value={expenseForm.description}
              onChange={(e) => setExpenseForm({ ...expenseForm, description: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Vendor Name</label>
              <input
                type="text"
                placeholder="e.g. SafeLift Logistics"
                value={expenseForm.vendor_name}
                onChange={(e) => setExpenseForm({ ...expenseForm, vendor_name: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Vendor Bill / Ref #</label>
              <input
                type="text"
                placeholder="e.g. INV-2026-99"
                value={expenseForm.invoice_reference}
                onChange={(e) => setExpenseForm({ ...expenseForm, invoice_reference: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowExpenseModal(false)}
              className="px-4 py-2 border border-stone-300 text-stone-700 rounded-lg text-sm hover:bg-stone-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-emerald-800 text-white rounded-lg text-sm font-medium hover:bg-emerald-900"
            >
              Post Expense to Ledger
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
