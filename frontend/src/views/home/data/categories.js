import stays from '../../../assets/image/home/stays.webp'
import travel from '../../../assets/image/home/travel.webp'
import cars from '../../../assets/image/home/cars.webp'
import beauty from '../../../assets/image/home/beauty.webp'
import health from '../../../assets/image/home/health.webp'
import services from '../../../assets/image/home/services.webp'
import pin from '../../../assets/image/home/pin.webp'

export const pinImage = pin

// مرکز مسیرها
export const HUB = { x: 53, y: 50 }

// ترتیب قرار گرفتن در صحنه (پین قبل از beauty می‌آید)
export const STAGE_ORDER = ['travel', 'stays', 'cars', 'beauty', 'health', 'services']

// x / y / w به درصدِ صحنه؛ icon محتوای داخل svg است
export const categories = [
  {
    id: 'stays', name: 'اقامت', x: 31.3, y: 25, w: 40, img: stays,
    icon: '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
  },
  {
    id: 'travel', name: 'سفر', x: 72.6, y: 21, w: 50, img: travel,
    icon: '<path d="M21 3L3 11l7 2 2 7z"/><path d="M10 13l11-10"/>',
  },
  {
    id: 'cars', name: 'خودرو', x: 17.1, y: 43.4, w: 33, img: cars,
    icon: '<path d="M4 16V12l2-5h12l2 5v4"/><path d="M3 16h18"/><circle cx="7.5" cy="17.5" r="1.5"/><circle cx="16.5" cy="17.5" r="1.5"/>',
  },
  {
    id: 'beauty', name: 'زیبایی', x: 80.6, y: 47.4, w: 38, img: beauty,
    icon: '<path d="M12 21c0-5-6-6-6-12 4 0 6 3 6 6 0-3 2-6 6-6 0 6-6 7-6 12z"/>',
  },
  {
    id: 'health', name: 'سلامت', x: 28.7, y: 72.4, w: 45, img: health,
    icon: '<path d="M9 3h6v6h6v6h-6v6H9v-6H3V9h6z"/>',
  },
  {
    id: 'services', name: 'خدمات', x: 75.6, y: 76.3, w: 48, img: services,
    icon: '<path d="M14 6l4-3 3 3-3 4"/><path d="M14 10L4 20"/><path d="M10 14l-3-3 2-5 4 1"/><path d="M5 19l2 2"/>',
  },
]