import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import { StageStepper } from '../components/StageStepper';
import { EligibilityBadge } from '../components/EligibilityBadge';

describe('StageStepper Component', () => {
  it('renders all 6 standard stages', () => {
    const { container } = render(<StageStepper currentStage="SHORTLISTED" />);
    expect(container.textContent).toContain('Applied');
    expect(container.textContent).toContain('Shortlisted');
    expect(container.textContent).toContain('Interview Scheduled');
    expect(container.textContent).toContain('Interviewed');
    expect(container.textContent).toContain('Offered');
    expect(container.textContent).toContain('Accepted');
  });
});

describe('EligibilityBadge Component', () => {
  it('renders Eligible to Apply when eligible', () => {
    const { container } = render(
      <EligibilityBadge 
        eligibility={{
          is_eligible: true,
          cgpa_pass: true,
          backlogs_pass: true,
          season_offer_pass: true,
          branch_pass: true,
          rejection_reasons: [],
          inputs_evaluated: {}
        }} 
      />
    );
    expect(container.textContent).toContain('Eligible to Apply');
  });

  it('renders Ineligible button with reason modal trigger when not eligible', () => {
    const { container } = render(
      <EligibilityBadge 
        eligibility={{
          is_eligible: false,
          cgpa_pass: false,
          backlogs_pass: true,
          season_offer_pass: true,
          branch_pass: true,
          rejection_reasons: ['CGPA below minimum'],
          inputs_evaluated: {}
        }} 
      />
    );
    expect(container.textContent).toContain('Ineligible (View Reason)');
  });
});
