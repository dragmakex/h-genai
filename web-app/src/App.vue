<script setup>
import SfilLogo from '@/assets/images/Sfil-Logo.png'
import { Button } from '@/components/ui/button'
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
import { Check, ChevronsUpDown } from 'lucide-vue-next'
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
</script>

<template>
  <div class="bg-slate-50 flex flex-col items-center h-screen space-y-4">
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
    <div class="w-full max-w-screen-lg flex-1 flex flex-col items-center py-2 px-8 pt-16 mt-2">
      <div>
        <!-- <div class="text-gray-500">Selectionnez un client.</div> -->
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
          <Button class="bg-[#164194]">Générer</Button>
        </div>
      </div>
    </div>
  </div>
</template>
