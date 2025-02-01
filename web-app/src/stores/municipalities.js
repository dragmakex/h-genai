import { defineStore } from 'pinia'
import records from '@/assets/records.json'

export const useMunicipalitiesStore = defineStore('municipalities', {
  state: () => ({
    municipalities: []
  }),
  actions: {
    initializeMunicipalities() {
      this.municipalities = records
    }
  },
  getters: {
    getMunicipalitiesForSelect: (state) => {
      return state.municipalities
        .map(municipality => ({
          code: municipality.com_code,
          name: municipality.com_name,
          inter_name: municipality.epci_name,
          inter_code: municipality.epci_code,
          siren: municipality.siren
        }))
    }
  }
})
