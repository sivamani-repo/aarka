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

    return children;
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
                    <Route path="dashboard" element={<DashboardPage />} />
                    <Route path="leads" element={<LeadsPage />} />
                    <Route path="customers" element={<CustomersPage />} />
                    <Route path="surveys" element={<SurveysPage />} />
                    <Route path="packages" element={<PackagesPage />} />
                    <Route path="quotations" element={<QuotationsPage />} />
                    <Route path="orders" element={<OrdersPage />} />
                    <Route path="payments" element={<PaymentsPage />} />
                    <Route path="inventory" element={<InventoryPage />} />
                    <Route path="serials" element={<SerialsPage />} />
                    <Route path="dispatch" element={<DispatchPage />} />
                    <Route path="technicians" element={<TechniciansPage />} />
                    <Route path="scheduling" element={<SchedulePage />} />
                    <Route path="installations" element={<InstallationsPage />} />
                    <Route path="warranties" element={<WarrantiesPage />} />
                    <Route path="service" element={<ServicePage />} />
                    <Route path="suppliers" element={<SuppliersPage />} />
                    <Route path="finance" element={<FinancePage />} />
                    <Route path="subsidies" element={<SubsidiesPage />} />
                    <Route path="reports" element={<ReportsPage />} />
                    <Route path="team" element={<TeamPage />} />
                    <Route path="settings" element={<SettingsPage />} />
                </Route>

                {/* Fallback */}
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
        </BrowserRouter>
    );
}
