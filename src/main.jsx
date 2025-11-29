import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'

// Pages
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import Members from './pages/Members'
import Ranking from './pages/Ranking'
import Tickets from './pages/Tickets'
import AdminPanel from './pages/AdminPanel'
import StaffLogin from './pages/StaffLogin'

const queryClient = new QueryClient()

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/members" element={<Members />} />
          <Route path="/ranking" element={<Ranking />} />
          <Route path="/tickets" element={<Tickets />} />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/login" element={<StaffLogin />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
