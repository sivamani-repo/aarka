import React, { useEffect, useState } from 'react';
import { Save, ShieldCheck, Building2, Sliders, CheckCircle2 } from 'lucide-react';

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    companyName: 'AARKA Solar Solutions Pvt. Ltd.',
    tagline: 'Solar Operations, Simplified.',
    gstin: '36AABCA1234F1Z5',
    contactEmail: 'operations@aarka.com',
    contactPhone: '+91 80088 12345',
    address: 'Plot 42, Hitec City Phase II, Hyderabad, Telangana 500081',
    // Warranty Policies (in months)
    moduleWarrantyMonths: 300, // 25 years
    inverterWarrantyMonths: 60, // 5 years
    batteryWarrantyMonths: 60,  // 5 years
    workmanshipWarrantyMonths: 24, // 2 years
    // Tax rates
    compositeSolarGst: 13.8, // 70% goods @ 12% + 30% service @ 18% = 13.8%
    serviceGst: 18.0,
    // Operational rules
    enforceSurveyApproval: true,
    enforceNinePointChecklist: true,
    enforceStrictSerialTracking: true,
  });

  const [saved, setSaved] = useState(false);

  useEffect(() => {
    try {
      const savedSettings = localStorage.getItem('aarka_settings');
      if (savedSettings) {
        setSettings((current) => ({ ...current, ...JSON.parse(savedSettings) }));
      }
    } catch (error) {
      console.error('Could not load saved settings:', error);
    }
  }, []);

  const handleSave = (e) => {
    e.preventDefault();
    localStorage.setItem('aarka_settings', JSON.stringify(settings));
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6 enterprise-page enterprise-settings-page">
      <div className="enterprise-page-header">
        <div className="enterprise-page-copy">
          <span className="enterprise-eyebrow">Administration · Platform configuration</span>
          <h1 className="text-2xl font-bold text-stone-900 tracking-tight">System Settings & Business Rules</h1>
          <p className="text-sm text-stone-600 mt-1">
            Configure enterprise operational parameters, statutory tax percentages, and standard warranty policies.
          </p>
        </div>
      </div>

      {saved && (
        <div className="p-4 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center gap-2 text-sm font-medium">
          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          Settings successfully persisted to application configuration.
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Company Profile */}
        <div className="enterprise-settings-card">
          <div className="flex items-center gap-2 pb-3 border-b border-stone-100">
            <Building2 className="w-5 h-5 text-emerald-800" />
            <h2 className="text-base font-bold text-stone-900">Organization & DISCOM Accreditation</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Company Legal Name</label>
              <input
                type="text"
                value={settings.companyName}
                onChange={(e) => setSettings({ ...settings, companyName: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Brand Tagline</label>
              <input
                type="text"
                value={settings.tagline}
                onChange={(e) => setSettings({ ...settings, tagline: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">GSTIN Number</label>
              <input
                type="text"
                value={settings.gstin}
                onChange={(e) => setSettings({ ...settings, gstin: e.target.value })}
                className="w-full px-3 py-2 text-sm font-mono border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Support Email</label>
              <input
                type="email"
                value={settings.contactEmail}
                onChange={(e) => setSettings({ ...settings, contactEmail: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Operations Phone</label>
              <input
                type="text"
                value={settings.contactPhone}
                onChange={(e) => setSettings({ ...settings, contactPhone: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Headquarters Address</label>
            <input
              type="text"
              value={settings.address}
              onChange={(e) => setSettings({ ...settings, address: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
            />
          </div>
        </div>

        {/* Standard Warranty Rules */}
        <div className="enterprise-settings-card">
          <div className="flex items-center gap-2 pb-3 border-b border-stone-100">
            <ShieldCheck className="w-5 h-5 text-emerald-800" />
            <h2 className="text-base font-bold text-stone-900">Standard Warranty Policies (Months)</h2>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">PV Modules (Months)</label>
              <input
                type="number"
                value={settings.moduleWarrantyMonths}
                onChange={(e) => setSettings({ ...settings, moduleWarrantyMonths: parseInt(e.target.value) })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none font-semibold"
              />
              <span className="text-[11px] text-stone-500">25 Years Standard</span>
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Inverters (Months)</label>
              <input
                type="number"
                value={settings.inverterWarrantyMonths}
                onChange={(e) => setSettings({ ...settings, inverterWarrantyMonths: parseInt(e.target.value) })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none font-semibold"
              />
              <span className="text-[11px] text-stone-500">5 Years Standard</span>
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Batteries (Months)</label>
              <input
                type="number"
                value={settings.batteryWarrantyMonths}
                onChange={(e) => setSettings({ ...settings, batteryWarrantyMonths: parseInt(e.target.value) })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none font-semibold"
              />
              <span className="text-[11px] text-stone-500">5 Years Standard</span>
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Workmanship (Months)</label>
              <input
                type="number"
                value={settings.workmanshipWarrantyMonths}
                onChange={(e) => setSettings({ ...settings, workmanshipWarrantyMonths: parseInt(e.target.value) })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none font-semibold"
              />
              <span className="text-[11px] text-stone-500">2 Years Standard</span>
            </div>
          </div>
        </div>

        {/* Statutory & Operational Rules */}
        <div className="enterprise-settings-card">
          <div className="flex items-center gap-2 pb-3 border-b border-stone-100">
            <Sliders className="w-5 h-5 text-emerald-800" />
            <h2 className="text-base font-bold text-stone-900">Statutory Tax & Operational Rule Engines</h2>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Composite Solar GST (%)</label>
              <input
                type="number"
                step="0.1"
                value={settings.compositeSolarGst}
                onChange={(e) => setSettings({ ...settings, compositeSolarGst: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
              <span className="text-[11px] text-stone-500">70% goods @ 12% + 30% service @ 18%</span>
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Standard Service GST (%)</label>
              <input
                type="number"
                step="0.1"
                value={settings.serviceGst}
                onChange={(e) => setSettings({ ...settings, serviceGst: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
              <span className="text-[11px] text-stone-500">Applicable to AMC & extra services</span>
            </div>
          </div>

          <div className="space-y-3 pt-2">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.enforceSurveyApproval}
                onChange={(e) => setSettings({ ...settings, enforceSurveyApproval: e.target.checked })}
                className="w-4 h-4 text-emerald-700 rounded border-stone-300 focus:ring-emerald-600"
              />
              <span className="text-sm font-medium text-stone-800">
                Rule #1: Block Quotation Finalization until Site Survey is APPROVED
              </span>
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.enforceStrictSerialTracking}
                onChange={(e) => setSettings({ ...settings, enforceStrictSerialTracking: e.target.checked })}
                className="w-4 h-4 text-emerald-700 rounded border-stone-300 focus:ring-emerald-600"
              />
              <span className="text-sm font-medium text-stone-800">
                Rule #7: Block Warehouse Dispatch until 100% of Serialized Items are Allocated
              </span>
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.enforceNinePointChecklist}
                onChange={(e) => setSettings({ ...settings, enforceNinePointChecklist: e.target.checked })}
                className="w-4 h-4 text-emerald-700 rounded border-stone-300 focus:ring-emerald-600"
              />
              <span className="text-sm font-medium text-stone-800">
                Rule #13 & #14: Enforce 9-Point Commissioning Checklist and Digital Signature before Handover
              </span>
            </label>
          </div>
        </div>

        <div className="enterprise-settings-footer">
          <button
            type="submit"
            className="inline-flex items-center gap-2 px-6 py-2.5 bg-emerald-800 hover:bg-emerald-900 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors"
          >
            <Save className="w-4 h-4" />
            Save Configurations
          </button>
        </div>
      </form>
    </div>
  );
}
