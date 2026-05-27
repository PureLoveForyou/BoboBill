<script setup>
import { computed } from 'vue'

let uidCounter = 0
function useId() {
  return `bl-${++uidCounter}`
}

const props = defineProps({
  size: {
    type: [Number, String],
    default: 40
  }
})

const id = useId()

const gradientIds = computed(() => ({
  walletBody: `${id}-walletBody`,
  cardBack: `${id}-cardBack`,
  cardMiddle: `${id}-cardMiddle`,
  cardFront: `${id}-cardFront`,
  buttonPlate: `${id}-buttonPlate`,
  softShadow: `${id}-softShadow`
}))
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 128 128"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    :aria-label="$attrs['aria-label'] ?? 'BoboBill Logo'"
    :class="$attrs.class"
  >
    <defs>
      <linearGradient :id="gradientIds.walletBody" x1="22" y1="104" x2="104" y2="18" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="#1F6BFF" />
        <stop offset="0.52" stop-color="#35BDF2" />
        <stop offset="1" stop-color="#5EE6B8" />
      </linearGradient>

      <linearGradient :id="gradientIds.cardBack" x1="45" y1="18" x2="106" y2="63" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="#5EE6B8" />
        <stop offset="1" stop-color="#23C7D9" />
      </linearGradient>

      <linearGradient :id="gradientIds.cardMiddle" x1="29" y1="28" x2="104" y2="70" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="#7DD3FC" />
        <stop offset="1" stop-color="#4EDDD1" />
      </linearGradient>

      <linearGradient :id="gradientIds.cardFront" x1="18" y1="42" x2="104" y2="78" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="#F7FBFF" />
        <stop offset="0.55" stop-color="#DCEBFF" />
        <stop offset="1" stop-color="#BEEFFF" />
      </linearGradient>

      <linearGradient :id="gradientIds.buttonPlate" x1="82" y1="72" x2="118" y2="100" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="#A8F2E1" stop-opacity="0.72" />
        <stop offset="1" stop-color="#6DCDF7" stop-opacity="0.72" />
      </linearGradient>

      <filter :id="gradientIds.softShadow" x="8" y="10" width="112" height="112" filterUnits="userSpaceOnUse">
        <feDropShadow dx="0" dy="10" stdDeviation="10" flood-color="#1F6BFF" flood-opacity="0.16" />
      </filter>
    </defs>

    <!-- Back card -->
    <path
      d="M47 21C49.5 13.5 57.1 9.4 65.1 11.2L96.8 18.4C105.7 20.4 112 28.3 112 37.4V78.5L47 65V21Z"
      :fill="`url(#${gradientIds.cardBack})`"
    />

    <!-- Middle card -->
    <path
      d="M28 32.5C29.7 24.8 37.3 19.8 45.1 21.2L91.2 29.6C103.2 31.8 112 42.3 112 54.5V82L28 70V32.5Z"
      :fill="`url(#${gradientIds.cardMiddle})`"
    />

    <!-- Front white receipt/card layer -->
    <path
      d="M18 48.5C20.5 39.8 29.3 34.6 38.2 36.6L88.2 47.8C102.1 50.9 112 63.3 112 77.5V88.5L18 75V48.5Z"
      :fill="`url(#${gradientIds.cardFront})`"
    />

    <!-- Wallet body -->
    <path
      d="M16 55.5C16 47.5 22.5 41 30.5 41H94C106.2 41 116 50.8 116 63V95C116 107.2 106.2 117 94 117H41C27.2 117 16 105.8 16 92V55.5Z"
      :fill="`url(#${gradientIds.walletBody})`"
      :filter="`url(#${gradientIds.softShadow})`"
    />

    <!-- Top opening highlight -->
    <path
      d="M18 52C28 42 42 44 57 48L89 56C103 59.5 111 68 116 79"
      stroke="white"
      stroke-width="5"
      stroke-linecap="round"
      opacity="0.92"
    />

    <!-- Wallet clasp plate -->
    <path
      d="M84 78C84 70.3 90.3 64 98 64H116V98H98C90.3 98 84 91.7 84 84V78Z"
      :fill="`url(#${gradientIds.buttonPlate})`"
    />

    <!-- Button -->
    <circle cx="98" cy="81" r="8.5" fill="white" opacity="0.96" />

    <!-- Subtle lower gloss -->
    <path
      d="M23 94C40 103 67 105 105 94"
      stroke="white"
      stroke-width="2"
      stroke-linecap="round"
      opacity="0.12"
    />
  </svg>
</template>
