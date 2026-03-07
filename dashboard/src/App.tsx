import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useSearchParams } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ActivityStream from './components/ActivityStream';
import NegotiationChat from './components/NegotiationChat';
import SurplusPanel from './components/SurplusPanel';
import IncomeComparison from './components/IncomeComparison';
import ProcessingImpact from './components/ProcessingImpact';
import PaymentMetrics from './components/PaymentMetrics';
import SatelliteData from './components/SatelliteData';
import DemoControls from './components/DemoControls';
import FarmerListPage from './pages/FarmerListPage';
import FarmerDetailPage from './pages/FarmerDetailPage';

const queryClient = new QueryClient();

function DashboardPage() {
  const [searchParams] = useSearchParams();
  const [workflowId, setWorkflowId] = useState<string | null>(null);

  useEffect(() => {
    const urlWorkflowId = searchParams.get('workflow_id');
    if (urlWorkflowId) {
      setWorkflowId(urlWorkflowId);
    }
  }, [searchParams]);

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-white text-xl font-bold">A</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Anna Drishti</h1>
                <p className="text-sm text-gray-500">AI-Assisted Selling for Farmers</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                to="/farmers"
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Farmer Portfolio
              </Link>
              <span className="px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-full">
                LIVE DEMO
              </span>
              {workflowId && (
                <span className="text-sm text-gray-600">
                  Workflow: {workflowId.slice(0, 8)}...
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Demo Controls */}
        <DemoControls onWorkflowStart={setWorkflowId} />

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
          {/* Left Column - Activity Stream */}
          <div className="lg:col-span-1">
            <ActivityStream workflowId={workflowId} />
          </div>

          {/* Middle Column - Negotiation, Surplus & Satellite */}
          <div className="lg:col-span-1 space-y-6">
            <NegotiationChat workflowId={workflowId} />
            <SurplusPanel workflowId={workflowId} />
            <SatelliteData workflowId={workflowId} />
          </div>

          {/* Right Column - Income, Impact & Payments */}
          <div className="lg:col-span-1 space-y-6">
            <IncomeComparison workflowId={workflowId} />
            <ProcessingImpact />
            <PaymentMetrics />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-500">
            Anna Drishti - Hackathon MVP Demo | Powered by AWS Bedrock, Lambda, DynamoDB
          </p>
        </div>
      </footer>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/farmers" element={<FarmerListPage />} />
          <Route path="/farmers/:farmerName" element={<FarmerDetailPage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
