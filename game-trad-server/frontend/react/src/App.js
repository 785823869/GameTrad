import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from './theme';

// 布局组件
import MainLayout from './components/layout/MainLayout';

// 页面组件
import Dashboard from './pages/Dashboard';
import OcrTool from './pages/OcrTool';
import RecipesManager from './pages/RecipesManager';
import LogViewer from './pages/LogViewer';
import UpdateManager from './pages/UpdateManager';
import Settings from './pages/Settings';
import NotFound from './pages/NotFound';

// 新增页面组件
import Inventory from './pages/Inventory';
import StockIn from './pages/StockIn';
import StockOut from './pages/StockOut';
import TradeMonitor from './pages/TradeMonitor';
import NvwaPrice from './pages/NvwaPrice';
import SilverPrice from './pages/SilverPrice';
import NewTrade from './pages/NewTrade';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="inventory" element={<Inventory />} />
            <Route path="stock-in" element={<StockIn />} />
            <Route path="stock-out" element={<StockOut />} />
            <Route path="trade-monitor" element={<TradeMonitor />} />
            <Route path="nvwa-price" element={<NvwaPrice />} />
            <Route path="silver-price" element={<SilverPrice />} />
            <Route path="ocr" element={<OcrTool />} />
            <Route path="recipes" element={<RecipesManager />} />
            <Route path="logs" element={<LogViewer />} />
            <Route path="updates" element={<UpdateManager />} />
            <Route path="settings" element={<Settings />} />
            <Route path="new-trade" element={<NewTrade />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App; 