import React from 'react';
import katex from 'katex';
import { useApp } from '../../context/AppContext';

export default function FormulasTab() {
  const { trace, activeExperimentId, currentExperiment } = useApp();

  const steps = trace?.steps || [];
  const expName = currentExperiment?.name || activeExperimentId || 'Active Simulation';

  const renderLatex = (latex, fallback) => {
    if (!latex) return fallback;
    try {
      return (
        <div
          dangerouslySetInnerHTML={{
            __html: katex.renderToString(latex, {
              displayMode: true,
              throwOnError: false,
            }),
          }}
        />
      );
    } catch (e) {
      return <div>{fallback || latex}</div>;
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header Info */}
      <div className="card p-5 border border-border-color bg-bg-card rounded-xl">
        <div className="flex justify-between items-center flex-wrap gap-2">
          <div>
            <h2 className="text-lg font-bold text-text-primary">
              Scientific Explainability & Formula Trace
            </h2>
            <p className="text-xs text-text-secondary mt-1">
              Inspect every mathematical formula, substitution of current input variables, scientific citations, and unit evaluations for <strong className="text-accent-cyan">{expName}</strong>:
            </p>
          </div>
          <span className="text-xs font-mono px-2.5 py-1 rounded bg-accent-primary/10 text-accent-primary border border-accent-primary/20">
            {steps.length} Derivation Steps
          </span>
        </div>
      </div>

      {/* Steps List */}
      {steps.length === 0 ? (
        <div className="card p-8 text-center text-text-muted bg-bg-card rounded-xl border border-dashed border-border-color">
          <p className="text-sm">No mathematical calculation trace found for this experiment.</p>
          <p className="text-xs mt-1">Run a new simulation to generate full step-by-step physics explainability.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {steps.map((step, idx) => {
            const stepTitle = step.step_id
              ? step.step_id.replace('step_', '').replace(/_/g, ' ').toUpperCase()
              : `STEP ${idx + 1}`;

            return (
              <div
                key={step.step_id || idx}
                className="card p-5 border border-border-color bg-bg-card rounded-xl space-y-3 hover:border-accent-primary/30 transition-colors"
              >
                {/* Step Header */}
                <div className="flex justify-between items-center pb-2 border-b border-border-color">
                  <h4 className="text-sm font-bold text-text-primary flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-accent-primary/20 text-accent-primary flex items-center justify-center text-[10px] font-mono">
                      {idx + 1}
                    </span>
                    <span>Step {idx + 1}: {stepTitle}</span>
                  </h4>
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-500/15 text-accent-green border border-emerald-500/30">
                    {step.stage_name || 'Physics Stage'}
                  </span>
                </div>

                {/* English Description */}
                <p className="text-xs text-text-secondary leading-relaxed">
                  {step.description}
                </p>

                {/* Formula Box */}
                <div className="p-3.5 bg-bg-secondary rounded-lg border border-border-color overflow-x-auto text-center font-mono text-sm text-text-primary">
                  {renderLatex(step.formula_latex, step.formula_text)}
                </div>

                {/* Substituted Values */}
                {step.substitution_text && (
                  <div className="p-2.5 bg-bg-primary rounded border border-border-color/60 text-xs text-text-muted font-mono">
                    <span className="text-text-secondary font-sans font-semibold">Values substituted: </span>
                    {step.substitution_text}
                  </div>
                )}

                {/* Evaluated Result */}
                <div className="flex items-center justify-between p-2.5 bg-emerald-500/5 rounded border border-emerald-500/20 text-xs">
                  <div>
                    <span className="font-semibold text-text-secondary">Result: </span>
                    <strong className="font-mono text-accent-green">{step.result_formatted}</strong>{' '}
                    <span className="text-text-muted text-[11px]">({step.units})</span>
                  </div>
                </div>

                {/* Physical Justification / Citation */}
                {step.why_necessary && (
                  <div className="text-[11.5px] text-text-muted italic border-l-2 border-accent-cyan/60 pl-3 py-0.5">
                    <strong className="not-italic text-accent-cyan font-medium">Physical Justification: </strong>
                    {step.why_necessary}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

