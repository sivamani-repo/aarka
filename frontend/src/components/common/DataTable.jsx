import React, { useState } from 'react';
import { Search, ChevronLeft, ChevronRight, Inbox, Loader2 } from 'lucide-react';

export const DataTable = ({
  columns,
  data = [],
  searchKey,
  searchPlaceholder = 'Search records...',
  title,
  subtitle,
  actions,
  className = '',
  loading = false,
  emptyMessage = 'No data currently available',
  pageSize = 10,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  const filteredData = data.filter((item) => {
    if (!searchTerm) return true;
    if (searchKey) {
      const val = item[searchKey];
      return String(val || '').toLowerCase().includes(searchTerm.toLowerCase());
    }
    // Search across all properties
    return Object.values(item).some((val) =>
      String(val || '').toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  const totalPages = Math.ceil(filteredData.length / pageSize) || 1;
  const startIndex = (currentPage - 1) * pageSize;
  const paginatedData = filteredData.slice(startIndex, startIndex + pageSize);

  return (
    <div className={`aarka-card ${className}`.trim()}>
      <div className="aarka-card-header" style={{ flexWrap: 'wrap', gap: '16px' }}>
        <div>
          {title && <h3 style={{ fontSize: '18px', fontWeight: '700' }}>{title}</h3>}
          {subtitle && (
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>
              {subtitle} ({filteredData.length} records)
            </p>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', minWidth: '240px' }}>
            <Search
              size={16}
              style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-light)',
              }}
            />
            <input
              type="text"
              className="form-control"
              style={{ paddingLeft: '36px', height: '38px', fontSize: '13px' }}
              placeholder={searchPlaceholder}
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
            />
          </div>
          {actions}
        </div>
      </div>

      <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
        {loading ? (
          <div style={{ padding: '48px 24px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <Loader2 className="animate-spin" size={24} style={{ margin: '0 auto 12px' }} />
            <p style={{ fontSize: '13px' }}>Loading records...</p>
          </div>
        ) : paginatedData.length === 0 ? (
          <div style={{ padding: '48px 24px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <Inbox size={40} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
            <h4 style={{ fontSize: '15px', fontWeight: '600', marginBottom: '4px' }}>No records found</h4>
            <p style={{ fontSize: '13px', color: 'var(--text-light)' }}>
              {searchTerm ? 'Try adjusting your search criteria' : emptyMessage}
            </p>
          </div>
        ) : (
          <table className="aarka-table">
            <thead>
              <tr>
                {columns.map((col, idx) => (
                  <th key={idx} style={{ width: col.width }}>
                    {col.header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {paginatedData.map((row, rowIdx) => (
                <tr key={row.id || rowIdx}>
                  {columns.map((col, colIdx) => (
                    <td key={colIdx}>
                      {col.render
                        ? col.render(row)
                        : col.cell
                          ? col.cell(row)
                          : typeof col.accessor === 'function'
                            ? col.accessor(row)
                            : row[col.accessor]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {totalPages > 1 && (
        <div
          style={{
            padding: '12px 20px',
            borderTop: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '13px',
            color: 'var(--text-muted)',
          }}
        >
          <span>
            Showing {startIndex + 1} to {Math.min(startIndex + pageSize, filteredData.length)} of {filteredData.length} records
          </span>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button
              className="btn btn-secondary btn-sm"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            >
              <ChevronLeft size={14} /> Prev
            </button>
            <button
              className="btn btn-secondary btn-sm"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            >
              Next <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataTable;
