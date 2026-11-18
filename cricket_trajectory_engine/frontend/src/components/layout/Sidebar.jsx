import React from 'react';
import { useApp } from '../../context/AppContext';
import { 
  BarChart3, 
  Settings2, 
  Compass, 
  FileCode2, 
  FolderClock, 
  Scale, 
  Video,
  Activity,
  X 
} from 'lucide-react';

export default function Sidebar() {
  const { activeTab, setActiveTab, mobileMenuOpen, setMobileMenuOpen } = useApp();

  const navItems = [
    { id: 'tab-dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'tab-new-experiment', label: 'New Experiment', icon: Settings2 },
    { id: 'tab-ground-view', label: '3D Ground View', icon: Compass },
    { id: 'tab-pose-study', label: 'Pose & Shot Analysis', icon: Activity },
    { id: 'tab-formulas', label: 'Formula Trace', icon: FileCode2 },
    { id: 'tab-history', label: 'Experiment History', icon: FolderClock },
    { id: 'tab-compare', label: 'Comparison & Delta', icon: Scale },
    { id: 'tab-videos', label: 'Video Analytics', icon: Video },
  ];

  const handleSelectTab = (id) => {
    setActiveTab(id);
    if (mobileMenuOpen) {
      setMobileMenuOpen(false);
    }
  };

  const sidebarContent = (
    <aside className="w-64 bg-bg-secondary border-r border-border-color flex flex-col flex-shrink-0 h-full transition-colors duration-300">
      {/* Brand Header */}
      <div className="p-4 border-b border-border-color flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full flex items-center justify-center text-lg flex-shrink-0 border border-white/20 shadow-[0_0_16px_rgba(244,63,94,0.4)] bg-gradient-to-br from-rose-500 via-rose-700 to-rose-900">
            🏏
          </div>
          <div>
            <div className="text-[13.5px] font-extrabold tracking-wider text-white uppercase bg-gradient-to-r from-white to-accent-primary bg-clip-text text-transparent">
              TRAJECTORY AI
            </div>
            <div className="text-[10.5px] text-accent-primary font-mono font-medium tracking-wide">
              Physics Engine v2.0
            </div>
          </div>
        </div>
        {/* Mobile close button */}
        <button
          onClick={() => setMobileMenuOpen(false)}
          className="lg:hidden p-1.5 text-text-muted hover:text-white rounded-lg hover:bg-white/10 transition-colors"
          aria-label="Close navigation"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Nav Menu */}
      <nav className="p-3 flex-1 overflow-y-auto space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => handleSelectTab(item.id)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-[13px] font-medium transition-all text-left ${
                isActive
                  ? 'bg-gradient-to-r from-accent-primary/15 to-transparent text-emerald-400 border-l-[3px] border-accent-primary border-t border-r border-b border-accent-primary/20 font-semibold'
                  : 'text-text-secondary hover:text-text-primary hover:bg-bg-card-hover border border-transparent'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-accent-primary' : 'text-text-muted'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Sidebar Footer */}
      <div className="p-3.5 border-t border-border-color text-[11px] text-text-muted bg-bg-secondary space-y-2">
        <div className="flex justify-between items-center">
          <span>Engine Status</span>
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-emerald-500/15 text-accent-green border border-emerald-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            Online
          </span>
        </div>
        <div className="flex justify-between items-center font-mono">
          <span>Database</span>
          <span className="text-accent-cyan font-semibold text-[11px]">SQLite Active</span>
        </div>
      </div>
    </aside>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <div className="hidden lg:flex flex-shrink-0 z-20">
        {sidebarContent}
      </div>

      {/* Mobile Slide-over Drawer Overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden">
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
            onClick={() => setMobileMenuOpen(false)}
          />
          {/* Drawer content */}
          <div className="relative z-10 flex">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}

