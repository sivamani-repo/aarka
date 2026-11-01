import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';

// Layout
import ApplicationLayout from './components/layout/ApplicationLayout';

// Pages
const LoginPage = lazy(() => import('./pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('./pages/auth/RegisterPage'));
const VerifyEmailPage = lazy(() => import('./pages/auth/VerifyEmailPage'));
const ForgotPasswordPage = lazy(() => import('./pages/auth/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('./pages/auth/ResetPasswordPage'));
const PublicEnquiryPage = lazy(() => import('./pages/public/PublicEnquiryPage'));
const DashboardPage = lazy(() => import('./pages/dashboard/DashboardPage'));
const LeadsPage = lazy(() => import('./pages/leads/LeadsPage'));
const CustomersPage = lazy(() => import('./pages/customers/CustomersPage'));
const SurveysPage = lazy(() => import('./pages/surveys/SurveysPage'));
const PackagesPage = lazy(() => import('./pages/packages/PackagesPage'));
const QuotationsPage = lazy(() => import('./pages/quotations/QuotationsPage'));
const OrdersPage = lazy(() => import('./pages/orders/OrdersPage'));
const PaymentsPage = lazy(() => import('./pages/payments/PaymentsPage'));
const InventoryPage = lazy(() => import('./pages/inventory/InventoryPage'));
const SerialsPage = lazy(() => import('./pages/serials/SerialsPage'));
const DispatchPage = lazy(() => import('./pages/dispatch/DispatchPage'));
const TechniciansPage = lazy(() => import('./pages/technicians/TechniciansPage'));
const SchedulePage = lazy(() => import('./pages/scheduling/SchedulePage'));
const InstallationsPage = lazy(() => import('./pages/installations/InstallationsPage'));
const WarrantiesPage = lazy(() => import('./pages/warranties/WarrantiesPage'));
const ServicePage = lazy(() => import('./pages/service/ServicePage'));
const SuppliersPage = lazy(() => import('./pages/suppliers/SuppliersPage'));
const FinancePage = lazy(() => import('./pages/finance/FinancePage'));
const SubsidiesPage = lazy(() => import('./pages/subsidies/SubsidiesPage'));
const ReportsPage = lazy(() => import('./pages/reports/ReportsPage'));
const TeamPage = lazy(() => import('./pages/team/TeamPage'));
const SettingsPage = lazy(() => import('./pages/settings/SettingsPage'));
const CompanyProfilePage = lazy(() => import('./pages/company/CompanyProfilePage'));

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

const RouteLoadingFallback = () => (
    <div className="min-h-screen bg-stone-100 flex items-center justify-center" role="status">
        <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-3 border-emerald-700 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-sm text-stone-600 font-medium">Loading AARKA...</p>
        </div>
    </div>
);

export default function App() {
    return (
        <BrowserRouter>
            <Suspense fallback={<RouteLoadingFallback />}>
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
            </Suspense>
        </BrowserRouter>
    );
}
