import { ref, computed } from 'vue'
import { CATEGORIES_WITH_ALL, PLATFORMS_WITH_ALL, PLATFORM_INFO } from '../constants/bill'

export function useBillFilters() {
  const selectedCategory = ref('all')
  const selectedPlatform = ref('all')

  const categoryOptions = computed(() =>
    CATEGORIES_WITH_ALL.map(cat => ({
      value: cat,
      label: cat === 'all' ? '全部分类' : cat
    }))
  )

  const platformOptions = computed(() =>
    PLATFORMS_WITH_ALL.map(plat => ({
      value: plat,
      label: plat === 'all' ? '全部平台' : PLATFORM_INFO[plat]?.name || plat
    }))
  )

  return {
    selectedCategory,
    selectedPlatform,
    categoryOptions,
    platformOptions
  }
}
