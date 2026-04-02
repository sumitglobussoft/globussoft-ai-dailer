import React from 'react';
import WhatsAppTab from '../components/tabs/WhatsAppTab';

export default function WhatsAppPage({ apiFetch, API_URL, orgProducts, selectedOrg, orgTimezone }) {
  return (
    <WhatsAppTab
      apiFetch={apiFetch} API_URL={API_URL}
      orgProducts={orgProducts} selectedOrg={selectedOrg}
      orgTimezone={orgTimezone}
    />
  );
}
