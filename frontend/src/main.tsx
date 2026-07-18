import React from 'react';
import ReactDOM from 'react-dom/client';
import Root from './AppRoutes';
import './index.css';
import './components/map/setupLeaflet';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);
