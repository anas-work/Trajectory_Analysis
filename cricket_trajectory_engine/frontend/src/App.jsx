import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import Layout from './components/layout/Layout';
import DashboardTab from './components/dashboard/DashboardTab';
import NewExperimentTab from './components/simulation/NewExperimentTab';
import GroundViewTab from './components/ground-view/GroundViewTab';
import FormulasTab from './components/formulas/FormulasTab';
import HistoryTab from './components/history/HistoryTab';
import ComparisonTab from './components/comparison/ComparisonTab';
import VideosTab from './components/videos/VideosTab';
import PoseStudyTab from './components/pose-study/PoseStudyTab';

function TabContent() {
  const { activeTab } = useApp();

  switch (activeTab) {
    case 'tab-dashboard':
      return <DashboardTab />;
    case 'tab-new-experiment':
      return <NewExperimentTab />;
    case 'tab-ground-view':
      return <GroundViewTab />;
    case 'tab-formulas':
      return <FormulasTab />;
    case 'tab-history':
      return <HistoryTab />;
    case 'tab-compare':
      return <ComparisonTab />;
    case 'tab-videos':
      return <VideosTab />;
    case 'tab-pose-study':
      return <PoseStudyTab />;
    default:
      return <DashboardTab />;
  }
}

export default function App() {
  return (
    <AppProvider>
      <Layout>
        <TabContent />
      </Layout>
    </AppProvider>
  );
}

