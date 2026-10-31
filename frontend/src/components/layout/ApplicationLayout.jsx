import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export const ApplicationLayout = () => {
  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-content">
        <Topbar />
        <main className="content-body">
          <Outlet />
        </main>
      </div>
    </div>
  );
};



export default ApplicationLayout;
