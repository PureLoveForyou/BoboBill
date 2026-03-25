<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    required: true
  },
  options: {
    type: Array,
    required: true
  },
  placeholder: {
    type: String,
    default: '请选择'
  }
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const dropdownRef = ref(null)

const selectedOption = computed(() => {
  return props.options.find(opt => {
    if (typeof opt === 'string') {
      return opt === props.modelValue
    }
    return opt.value === props.modelValue
  })
})

const displayLabel = computed(() => {
  if (!selectedOption.value) return props.placeholder
  if (typeof selectedOption.value === 'string') {
    return selectedOption.value
  }
  return selectedOption.value.label
})

const selectOption = (option) => {
  const value = typeof option === 'string' ? option : option.value
  emit('update:modelValue', value)
  isOpen.value = false
}

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const handleClickOutside = (e) => {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div ref="dropdownRef" class="relative">
    <button
      @click="toggleDropdown"
      class="flex items-center justify-between gap-2 px-4 py-3 rounded-xl bg-base-200/50 hover:bg-base-200/70 border-0 text-sm transition-all duration-200 min-w-[100px]"
      :class="{ 'ring-2 ring-primary/30': isOpen }"
    >
      <span class="truncate">{{ displayLabel }}</span>
      <svg 
        class="w-4 h-4 text-base-content/40 transition-transform duration-200"
        :class="{ 'rotate-180': isOpen }"
        fill="none" 
        viewBox="0 0 24 24" 
        stroke="currentColor" 
        stroke-width="2"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
      </svg>
    </button>
    
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 scale-95 -translate-y-2"
      enter-to-class="opacity-100 scale-100 translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 scale-100 translate-y-0"
      leave-to-class="opacity-0 scale-95 -translate-y-2"
    >
      <div 
        v-if="isOpen"
        class="absolute top-full left-0 mt-2 w-full min-w-[120px] py-2 rounded-2xl bg-base-100 shadow-xl border border-base-200/50 z-50 overflow-hidden"
      >
        <button
          v-for="(option, index) in options"
          :key="index"
          @click="selectOption(option)"
          class="w-full px-4 py-2.5 text-left text-sm hover:bg-base-200/50 transition-colors flex items-center justify-between"
          :class="{ 'bg-primary/10 text-primary': modelValue === (typeof option === 'string' ? option : option.value) }"
        >
          <span>{{ typeof option === 'string' ? option : option.label }}</span>
          <svg 
            v-if="modelValue === (typeof option === 'string' ? option : option.value)"
            class="w-4 h-4 text-primary"
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor" 
            stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </button>
      </div>
    </Transition>
  </div>
</template>
