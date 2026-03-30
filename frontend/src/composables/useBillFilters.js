import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { CATEGORIES_WITH_ALL, PLATFORMS_WITH_ALL } from '../constants/bill'

export function useBillFilters() {
  const { t } = useI18n()
  const selectedCategory = ref('all')
  const selectedPlatform = ref('all')

  const categoryOptions = computed(() =>
    CATEGORIES_WITH_ALL.map(cat => ({
      value: cat,
      label: cat === 'all' ? t('common.allCategories') : t('categories.' + cat)
    }))
  )

  const platformOptions = computed(() =>
    PLATFORMS_WITH_ALL.map(plat => ({
      value: plat,
      label: plat === 'all' ? t('common.allPlatforms') : t('platforms.' + plat)
    }))
  )

  return {
    selectedCategory,
    selectedPlatform,
    categoryOptions,
    platformOptions
  }
}
