import { defineStore } from 'pinia'

export const useUserSelectionStore = defineStore('userSelection', {
  state: () => ({
    selected_municipality: '',
    selected_municipality_code: '',
    selected_inter_municipality: '',
    selected_inter_municipality_code: '',
    selected_siren: ''
  }),
  actions: {
    setSelectedMunicipality(municipality) {
      this.selected_municipality = municipality.name
      this.selected_municipality_code = municipality.code
      this.selected_inter_municipality = municipality.inter_name || ''
      this.selected_inter_municipality_code = municipality.inter_code || ''
      this.selected_siren = municipality.siren || ''
    }
  }
})
