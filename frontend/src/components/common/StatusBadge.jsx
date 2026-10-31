import React from 'react';

export const StatusBadge = ({ status }) => {
  if (!status) return null;

  const normalized = String(status).toUpperCase();

  let badgeClass = 'badge-neutral';

  if (
    [
      'APPROVED',
      'COMPLETED',
      'CUSTOMER_ACCEPTED',
      'COVERED',
      'PAID',
      'VERIFIED',
      'ACTIVE',
      'RESOLVED',
      'CLOSED',
      'DELIVERED',
      'AVAILABLE',
      'APPROVED_BY_OEM',
      'REPAIRED'
    ].includes(normalized)
  ) {
    badgeClass = 'badge-success';
  } else if (
    [
      'PENDING',
      'DRAFT',
      'UNDER_REVIEW',
      'IN_PROGRESS',
      'QUALIFIED',
      'SCHEDULED',
      'MATERIAL_RESERVED',
      'READY_FOR_DISPATCH',
      'TESTING',
      'WAITING_FOR_PARTS',
      'EXPIRING_SOON',
      'PENDING_ACTIVATION'
    ].includes(normalized)
  ) {
    badgeClass = 'badge-warning';
  } else if (
    [
      'REJECTED',
      'EXPIRED',
      'LOST',
      'CANCELLED',
      'CRITICAL',
      'HIGH',
      'RETURNED_DEFECTIVE',
      'CLAIM_RAISED'
    ].includes(normalized)
  ) {
    badgeClass = 'badge-danger';
  } else if (
    [
      'NEW',
      'CONTACTED',
      'SENT',
      'ACCEPTED',
      'CONFIRMED',
      'DISPATCHED',
      'ASSIGNED',
      'REPLACEMENT_IN_PROGRESS'
    ].includes(normalized)
  ) {
    badgeClass = 'badge-info';
  }

  return (
    <span className={`badge ${badgeClass}`}>
      {status.replace(/_/g, ' ')}
    </span>
  );
};

export default StatusBadge;


