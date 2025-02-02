<script setup>
import SfilLogo from '@/assets/images/Sfil-Logo.png'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList
} from '@/components/ui/command'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { cn } from '@/lib/utils'
import { ref, computed, onMounted } from 'vue'
import { Check, ChevronsUpDown, LoaderCircle } from 'lucide-vue-next'
import { useUserSelectionStore } from '@/stores/userSelection'
import { useMunicipalitiesStore } from '@/stores/municipalities'

const userSelectionStore = useUserSelectionStore()
const municipalitiesStore = useMunicipalitiesStore()

onMounted(() => {
  municipalitiesStore.initializeMunicipalities()
})

const open = ref(false)
const value = computed({
  get: () => userSelectionStore.selected_municipality_code,
  set: (newValue) => userSelectionStore.setSelectedMunicipality(newValue)
})

const clients = computed(() => municipalitiesStore.getMunicipalitiesForSelect)

const isGenerating = ref(false)
const progress = ref(0)
const progressMessages = ref([
  "Recherche de données générales...",
  "Recherche de projets...",
  "Recherche de données financières...",
  "Recherche du budget primitif...",
  "Recherche de communes similaires...",
  "Génération du fichier...",
])

const error = ref(null)
const gotResult = ref(false)
const pdfUrl = ref(null)

const handleGenerate = async () => {
  isGenerating.value = true
  progress.value = 0
  gotResult.value = false
  error.value = null
  
  const progressInterval = setInterval(() => {
    let increment
    if (progress.value < 20) {
      increment = Math.random() * 0.8 + 0.2
    } else if (progress.value < 40) {
      increment = Math.random() * 0.5 + 0.1
    } else if (progress.value < 60) {
      increment = Math.random() * 0.3 + 0.05
    } else if (progress.value < 80) {
      increment = Math.random() * 0.2 + 0.02
    } else {
      increment = Math.random() * 0.1 + 0.01
    }
    
    if (Math.random() < 0.2) {
      return
    }
    
    progress.value = Math.min(90, progress.value + increment)
  }, 200)

  try {
    const response = await fetch('https://kbba87ikh5.execute-api.us-west-2.amazonaws.com/generate-pdf', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        siren: userSelectionStore.selected_siren,
        municipality_name: userSelectionStore.selected_municipality,
        municipality_code: userSelectionStore.selected_municipality_code,
        inter_municipality_name: userSelectionStore.selected_inter_municipality,
        inter_municipality_code: userSelectionStore.selected_inter_municipality_code,
        reference_sirens: userSelectionStore.selected_reference_sirens
      })
    })

    if (!response.ok) {
      throw new Error('Erreur lors de la génération du PDF')
    }

    const blob = await response.blob()
    pdfUrl.value = URL.createObjectURL(blob)

    progress.value = 100
    
    setTimeout(() => {
      clearInterval(progressInterval)
      isGenerating.value = false
      progress.value = 0
      gotResult.value = true
    }, 1000)

  } catch (err) {
    console.error('Erreur:', err)
    clearInterval(progressInterval)
    error.value = err.message || "Une erreur s'est produite lors de la génération du PDF"
    
    // Debug logs
    console.log('error.value:', error.value)
    console.log('Is error truthy?:', !!error.value)
    console.log('Type of error:', typeof error.value)
    
    isGenerating.value = false
    progress.value = 0
  }
}
</script>

<template>
  <div class="bg-slate-50 flex flex-col items-center min-h-screen space-y-4">
    <div class="w-full max-w-screen-lg flex justify-between items-center py-2 px-8 mt-2">
      <div class="flex-shrink-0">
        <img :src="SfilLogo" alt="SFIL Logo" class="w-48" />
      </div>
      <div class="ml-16">
        <div class="text-3xl font-bold text-gray-700">Générateur de Fiches Clients</div>
        <div class="text-gray-500">Simplifiez la gestion des informations clients en un clic.</div>
      </div>
    </div>
    <hr class="w-full max-w-screen-lg">
    <div class="w-full max-w-screen-lg flex-1 flex flex-col items-center py-2 px-8 pt-8 mt-2">
      <div>
        <div class="flex space-x-2">
          <Popover v-model:open="open">
            <PopoverTrigger as-child>
              <Button
                variant="outline"
                role="combobox"
                :aria-expanded="open"
                class="w-[400px] justify-between"
              >
                {{ userSelectionStore.selected_municipality || "Sélectionnez un client..." }}
                <ChevronsUpDown class="ml-2 h-4 w-4 shrink-0 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent class="w-[400px] p-0">
              <Command>
                <CommandInput class="h-9" placeholder="Recherchez un client..." />
                <CommandEmpty>Aucun client trouvé.</CommandEmpty>
                <CommandList>
                  <CommandGroup>
                    <CommandItem
                      v-for="client in clients"
                      :key="client.code"
                      :value="client.name"
                      @select="(ev) => {
                        if (typeof ev.detail.value === 'string') {
                          userSelectionStore.setSelectedMunicipality(client)
                        }
                        open = false
                      }"
                    >
                      {{ client.name }}
                      <Check
                        :class="cn(
                          'ml-auto h-4 w-4',
                          value === client.code ? 'opacity-100' : 'opacity-0',
                        )"
                      />
                    </CommandItem>
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
          <Button 
            class="bg-[#164194]" 
            @click="handleGenerate"
            :disabled="isGenerating || !userSelectionStore.selected_municipality"
          >
            <span v-if="isGenerating" class="mr-2">
              <LoaderCircle class="animate-spin" />
            </span>
            Générer
          </Button>
        </div>
        <div v-if="isGenerating" class="mt-4 w-full">
          <Progress :model-value="progress" class="[&>*]:bg-[#1640948d] h-2" />
        </div>
        <div v-if="isGenerating">
          <div class="text-gray-500 mt-2">
            <p>{{ progressMessages[Math.min(progressMessages.length - 1, Math.floor((progress / 90) * (progressMessages.length - 1)))] }}</p>
          </div>
        </div>
        <div v-if="error" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <div class="flex items-center text-red-700">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
            <span class="font-medium">Erreur:</span>
            <span class="ml-2">{{ error }}</span>
          </div>
        </div>
        <div v-if="gotResult" class="mt-4 w-full">
          <div class="text-[#95BB20] flex items-center gap-2">
            <Check class="w-4 h-4" />
            <p> Fichier généré pour <b>{{ userSelectionStore.selected_municipality }}</b> avec succès.</p>
          </div>
        </div>
      </div>
      <div v-if="gotResult" class="w-full my-8">
        <div class="w-full h-[1000px]">
          <embed
            v-if="pdfUrl"
            :src="pdfUrl"
            class="w-full h-full"
            :title="`PDF pour ${userSelectionStore.selected_municipality}`"
            frameborder="0"
          ></embed>
        </div>
      </div>
    </div>
  </div>
</template>
