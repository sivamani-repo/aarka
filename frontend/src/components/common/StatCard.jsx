import React from 'react';

export const StatCard = ({ title, value, subtext, icon: Icon, change, isPositive, color = 'primary' }) => {
  return (
    <div className="aarka-card" style={{ padding: '20px 22px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          {title}
        </span>
        {Icon && (
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: 'var(--radius-md)',
              background: color === 'accent' ? 'var(--color-amber-50)' : 'var(--color-primary-50)',
              color: color === 'accent' ? 'var(--color-amber-600)' : 'var(--color-primary-700)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Icon size={20} />
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
        <span style={{ fontSize: '26px', fontWeight: '800', fontFamily: 'var(--font-display)', color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
          {value}
        </span>
        {change && (
          <span
            style={{
              fontSize: '12px',
              fontWeight: '600',
              color: isPositive ? 'var(--color-primary-600)' : 'var(--color-rose-600)',
            }}
          >
            {change}
          </span>
        )}
      </div>

      {subtext && (
        <div style={{ fontSize: '12px', color: 'var(--text-light)', marginTop: '4px' }}>
          {subtext}
        </div>
      )}
    </div>
  );
};

export default StatCard;


