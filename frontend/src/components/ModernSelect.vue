<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    required: true
  },
  options: {
    type: Array,
    required: true
  },
  placeholder: {
    type: String,
    default: '请选择'
  },
  label: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const selectRef = ref(null)

const selectedOption = computed(() => {
  return props.options.find(opt => opt.value === props.modelValue)
})

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const selectOption = (option) => {
  emit('update:modelValue', option.value)
  isOpen.value = false
}

const handleClickOutside = (event) => {
  if (selectRef.value && !selectRef.value.contains(event.target)) {
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
  <div ref="selectRef" class="relative" style="z-index: 9999;">
    <button
      @click="toggleDropdown"
      class="flex items-center justify-between w-full px-4 py-2.5 bg-base-100 border border-base-200/50 rounded-xl font-medium text-base-content hover:border-base-300/50 focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
      :class="{ 'ring-2 ring-primary/20 border-primary/30': isOpen }"
    >
      <span :class="selectedOption ? 'text-base-content' : 'text-base-content/50'">
        {{ selectedOption ? selectedOption.label : placeholder }}
      </span>
      <svg
        class="w-4 h-4 transition-transform duration-300"
        :class="isOpen ? 'rotate-180' : ''"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-1"
    >
      <div
        v-if="isOpen"
        class="absolute z-[9999] w-full mt-2 bg-base-100 border border-base-200/50 rounded-xl shadow-2xl overflow-hidden"
      >
        <div class="max-h-60 overflow-y-auto">
          <button
            v-for="option in options"
            :key="option.value"
            @click="selectOption(option)"
            class="w-full px-4 py-2.5 text-left hover:bg-base-200/50 transition-colors duration-200"
            :class="modelValue === option.value ? 'bg-primary/10 text-primary font-semibold' : 'text-base-content'"
          >
            {{ option.label }}
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>
