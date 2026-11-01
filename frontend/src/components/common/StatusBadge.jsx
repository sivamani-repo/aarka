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
      'REPAIRED',
      'DISBURSED',
      'COMMISSIONED',
      'FEASIBILITY_APPROVED',
      'VERIFIED_BY_AARKA',
      'READY_FOR_SUBMISSION',
      'POTENTIALLY_ELIGIBLE'
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
      'PENDING_ACTIVATION',
      'DOCUMENTS_PENDING',
      'UNDER_INTERNAL_REVIEW',
      'SUBMITTED',
      'FEASIBILITY_PENDING',
      'INSPECTION_PENDING',
      'SUBSIDY_CLAIM_PENDING',
      'MORE_INFO_REQUIRED',
      'REQUIRES_CONFIRMATION'
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
      'CLAIM_RAISED',
      'FEASIBILITY_REJECTED',
      'RE_UPLOAD_REQUIRED',
      'POTENTIALLY_NOT_ELIGIBLE'
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


