import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  UserCheck,
  ClipboardCheck,
  Package,
  FileText,
  ShoppingCart,
  CreditCard,
  Boxes,
  Barcode,
  Truck,
  Wrench,
  Calendar,
  Zap,
  ShieldCheck,
  Headphones,
  Building2,
  TrendingUp,
  Landmark,
  BarChart3,
  UserCog,
  Settings,
  SunMedium,
  ExternalLink
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Sidebar = () => {
  const { user } = useAuth();

  const navSections = [
    {
      title: 'CORE SALES',
      items: [
        { name: 'Dashboard', path: '/', icon: LayoutDashboard },
        { name: 'Leads', path: '/leads', icon: Users },
        { name: 'Customers', path: '/customers', icon: UserCheck },
        { name: 'Site Surveys', path: '/surveys', icon: ClipboardCheck },
      ],
    },
    {
      title: 'COMMERCIAL',
      items: [
        { name: 'Solar Packages', path: '/packages', icon: Package },
        { name: 'Quotations', path: '/quotations', icon: FileText },
        { name: 'Sales Orders', path: '/orders', icon: ShoppingCart },
        { name: 'Payments', path: '/payments', icon: CreditCard },
      ],
    },
    {
      title: 'WAREHOUSE & ASSETS',
      items: [
        { name: 'Inventory', path: '/inventory', icon: Boxes },
        { name: 'Serial Numbers', path: '/serials', icon: Barcode },
        { name: 'Warehouse Dispatch', path: '/dispatch', icon: Truck },
        { name: 'Suppliers', path: '/suppliers', icon: Building2 },
      ],
    },
    {
      title: 'FIELD OPERATIONS',
      items: [
        { name: 'Technicians', path: '/technicians', icon: Wrench },
        { name: 'Installation Schedule', path: '/schedule', icon: Calendar },
        { name: 'Installations', path: '/installations', icon: Zap },
      ],
    },
    {
      title: 'AFTER-SALES & SERVICE',
      items: [
        { name: 'Warranties', path: '/warranties', icon: ShieldCheck },
        { name: 'Service Tickets', path: '/service', icon: Headphones },
      ],
    },
    {
      title: 'FINANCE & GOVERNANCE',
      items: [
        { name: 'Finance & Margins', path: '/finance', icon: TrendingUp },
        { name: 'Govt Subsidies', path: '/subsidies', icon: Landmark },
        { name: 'Analytics & Reports', path: '/reports', icon: BarChart3 },
      ],
    },
    {
      title: 'ADMINISTRATION',
      items: [
        { name: 'Team Management', path: '/team', icon: UserCog },
        { name: 'Settings', path: '/settings', icon: Settings },
      ],
    },
  ];

  return (
    <aside
      className="app-sidebar"
      style={{
        backgroundColor: '#0c2318', // Deep forest green
        color: '#e2ede7',
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid #163827',
        flexShrink: 0,
        userSelect: 'none',
      }}
    >
      <NavLink
        to="/company-profile"
        className={({ isActive }) =>
          `sidebar-brand-link${isActive ? ' is-active' : ''}`
        }
        aria-label="AARKA company profile"
      >
        <div
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'linear-flex(135deg, #2e8b60, #f59e0b)',
            backgroundColor: '#2e8b60',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#ffffff',
            boxShadow: '0 2px 6px rgba(46, 139, 96, 0.4)',
          }}
        >
          <SunMedium size={22} color="#fef08a" />
        </div>
        <div>
          <div
            style={{
              fontSize: '18px',
              fontWeight: '800',
              letterSpacing: '0.04em',
              color: '#ffffff',
              fontFamily: 'var(--font-display)',
            }}
          >
            AARKA
          </div>
          <div style={{ fontSize: '11px', color: '#94bca7', fontWeight: '500' }}>
            Solar Operations, Simplified.
          </div>
        </div>
      </NavLink>

      {/* Navigation List */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '12px 10px',
        }}
      >
        {navSections.map((sec, idx) => (
          <div key={idx} style={{ marginBottom: '16px' }}>
            <div
              style={{
                fontSize: '10px',
                fontWeight: '700',
                color: '#6c9680',
                letterSpacing: '0.08em',
                padding: '6px 12px 4px',
                textTransform: 'uppercase',
              }}
            >
              {sec.title}
            </div>
            {sec.items.map((item, itemIdx) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={itemIdx}
                  to={item.path}
                  end={item.path === '/'}
                  className={({ isActive }) =>
                    `sidebar-nav-link${isActive ? ' is-active' : ''}`
                  }
                >
                  <Icon size={16} />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </div>
        ))}
      </div>

      {/* Public Portal Link & Version Footer */}
      <div
        style={{
          padding: '14px 16px',
          borderTop: '1px solid #163827',
          backgroundColor: '#091c13',
        }}
      >
        <a
          href="/enquiry"
          target="_blank"
          rel="noreferrer"
          className="sidebar-portal-link"
          style={{
            marginBottom: '10px',
          }}
        >
          <span>Public Customer Enquiry</span>
          <ExternalLink size={14} />
        </a>
        <div style={{ fontSize: '11px', color: '#5f8471', textAlign: 'center' }}>
          AARKA Platform v2.0 • Hackathon Edition
        </div>
      </div>
    </aside>
  );
};



export default Sidebar;
