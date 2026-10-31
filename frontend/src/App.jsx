import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';

// Layout
import ApplicationLayout from './components/layout/ApplicationLayout';

// Pages
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import VerifyEmailPage from './pages/auth/VerifyEmailPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';
import ResetPasswordPage from './pages/auth/ResetPasswordPage';

import PublicEnquiryPage from './pages/public/PublicEnquiryPage';
import DashboardPage from './pages/dashboard/DashboardPage';
import LeadsPage from './pages/leads/LeadsPage';
import CustomersPage from './pages/customers/CustomersPage';
import SurveysPage from './pages/surveys/SurveysPage';
import PackagesPage from './pages/packages/PackagesPage';
import QuotationsPage from './pages/quotations/QuotationsPage';
import OrdersPage from './pages/orders/OrdersPage';
import PaymentsPage from './pages/payments/PaymentsPage';
import InventoryPage from './pages/inventory/InventoryPage';
import SerialsPage from './pages/serials/SerialsPage';
import DispatchPage from './pages/dispatch/DispatchPage';
import TechniciansPage from './pages/technicians/TechniciansPage';
import SchedulePage from './pages/scheduling/SchedulePage';
import InstallationsPage from './pages/installations/InstallationsPage';
import WarrantiesPage from './pages/warranties/WarrantiesPage';
import ServicePage from './pages/service/ServicePage';
import SuppliersPage from './pages/suppliers/SuppliersPage';
import FinancePage from './pages/finance/FinancePage';
import SubsidiesPage from './pages/subsidies/SubsidiesPage';
import ReportsPage from './pages/reports/ReportsPage';
import TeamPage from './pages/team/TeamPage';
import SettingsPage from './pages/settings/SettingsPage';
import CompanyProfilePage from './pages/company/CompanyProfilePage';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
    const { user, loading } = useAuth();

    if (loading) {
        return (
            <div className="min-h-screen bg-stone-100 flex items-center justify-center">
                <div className="flex flex-col items-center gap-3">
                    <div className="w-8 h-8 border-3 border-emerald-700 border-t-transparent rounded-full animate-spin"></div>
                    <p className="text-sm text-stone-600 font-medium">Verifying AARKA Session...</p>
                </div>
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }
    if (user.role === 'Customer') {
        return <Navigate to="/enquiry" replace />;
    }

    return children;
};

const AUTHORIZED_PAGES = [
    { resource: 'dashboard', path: '/dashboard' },
    { resource: 'leads', path: '/leads' },
    { resource: 'customers', path: '/customers' },
    { resource: 'surveys', path: '/surveys' },
    { resource: 'products', path: '/packages' },
    { resource: 'quotations', path: '/quotations' },
    { resource: 'orders', path: '/orders' },
    { resource: 'payments', path: '/payments' },
    { resource: 'inventory', path: '/inventory' },
    { resource: 'serials', path: '/serials' },
    { resource: 'dispatches', path: '/dispatch' },
    { resource: 'technicians', path: '/technicians' },
    { resource: 'installations', path: '/installations' },
    { resource: 'warranties', path: '/warranties' },
    { resource: 'service', path: '/service' },
    { resource: 'suppliers', path: '/suppliers' },
    { resource: 'finance', path: '/finance' },
    { resource: 'subsidies', path: '/subsidies' },
    { resource: 'reports', path: '/reports' },
    { resource: 'employees', path: '/team' },
    { resource: 'settings', path: '/settings' },
];

const AuthorizedPage = ({ resource, children }) => {
    const { hasPermission } = useAuth();
    if (hasPermission(resource)) return children;

    const firstAuthorizedPage = AUTHORIZED_PAGES.find((page) =>
        hasPermission(page.resource)
    );
    return <Navigate to={firstAuthorizedPage?.path || '/company-profile'} replace />;
};

export default function App() {
    return (
        <BrowserRouter>
            <Routes>
                {/* Public & Authentication Routes */}
                <Route path="/enquiry" element={<PublicEnquiryPage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/verify-email" element={<VerifyEmailPage />} />
                <Route path="/forgot-password" element={<ForgotPasswordPage />} />
                <Route path="/reset-password" element={<ResetPasswordPage />} />

                {/* Protected SaaS Application Routes */}
                <Route
                    path="/"
                    element={
                        <ProtectedRoute>
                            <ApplicationLayout />
                        </ProtectedRoute>
                    }
                >
                    <Route index element={<Navigate to="/dashboard" replace />} />
                    <Route path="company-profile" element={<CompanyProfilePage />} />
                    <Route path="dashboard" element={<AuthorizedPage resource="dashboard"><DashboardPage /></AuthorizedPage>} />
                    <Route path="leads" element={<AuthorizedPage resource="leads"><LeadsPage /></AuthorizedPage>} />
                    <Route path="customers" element={<AuthorizedPage resource="customers"><CustomersPage /></AuthorizedPage>} />
                    <Route path="surveys" element={<AuthorizedPage resource="surveys"><SurveysPage /></AuthorizedPage>} />
                    <Route path="packages" element={<AuthorizedPage resource="products"><PackagesPage /></AuthorizedPage>} />
                    <Route path="quotations" element={<AuthorizedPage resource="quotations"><QuotationsPage /></AuthorizedPage>} />
                    <Route path="orders" element={<AuthorizedPage resource="orders"><OrdersPage /></AuthorizedPage>} />
                    <Route path="payments" element={<AuthorizedPage resource="payments"><PaymentsPage /></AuthorizedPage>} />
                    <Route path="inventory" element={<AuthorizedPage resource="inventory"><InventoryPage /></AuthorizedPage>} />
                    <Route path="serials" element={<AuthorizedPage resource="serials"><SerialsPage /></AuthorizedPage>} />
                    <Route path="dispatch" element={<AuthorizedPage resource="dispatches"><DispatchPage /></AuthorizedPage>} />
                    <Route path="technicians" element={<AuthorizedPage resource="technicians"><TechniciansPage /></AuthorizedPage>} />
                    <Route path="scheduling" element={<AuthorizedPage resource="installations"><SchedulePage /></AuthorizedPage>} />
                    <Route path="installations" element={<AuthorizedPage resource="installations"><InstallationsPage /></AuthorizedPage>} />
                    <Route path="warranties" element={<AuthorizedPage resource="warranties"><WarrantiesPage /></AuthorizedPage>} />
                    <Route path="service" element={<AuthorizedPage resource="service"><ServicePage /></AuthorizedPage>} />
                    <Route path="suppliers" element={<AuthorizedPage resource="suppliers"><SuppliersPage /></AuthorizedPage>} />
                    <Route path="finance" element={<AuthorizedPage resource="finance"><FinancePage /></AuthorizedPage>} />
                    <Route path="subsidies" element={<AuthorizedPage resource="subsidies"><SubsidiesPage /></AuthorizedPage>} />
                    <Route path="reports" element={<AuthorizedPage resource="reports"><ReportsPage /></AuthorizedPage>} />
                    <Route path="team" element={<AuthorizedPage resource="employees"><TeamPage /></AuthorizedPage>} />
                    <Route path="settings" element={<AuthorizedPage resource="settings"><SettingsPage /></AuthorizedPage>} />
                </Route>

                {/* Fallback */}
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
        </BrowserRouter>
    );
}
