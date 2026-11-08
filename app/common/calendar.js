import { loadResource } from '../../static/utils/resources.js';

let assets;
function loadAssets(path) {
  if (!assets) {
    assets = (async () => {
      await loadResource(`${path}/luxon-3.7.2.min.js`);
      await loadResource(`${path}/fullcalendar-6.1.19.global.min.js`);
      await loadResource(`${path}/ko-6.1.19.global.min.js`);
      await loadResource(`${path}/luxon3-6.1.19.global.min.js`);
    })().catch(error => { assets = null; throw error; });
  }
  return assets;
}

export default {
  template: '<div></div>',
  props: { events: Array, resourcePath: String },
  emits: ['date_click', 'event_click', 'event_change', 'period_change', 'load_error'],
  async mounted() {
    await this.$nextTick();
    try {
      await loadAssets(window.path_prefix + this.resourcePath);
      if (this.disposed) return;
      this.calendar = new FullCalendar.Calendar(this.$el, {
        initialView: 'dayGridMonth', timeZone: 'Asia/Seoul', locale: 'ko',
        buttonText: {today: '오늘', month: '월', week: '주', day: '일'},
        headerToolbar: {left: 'prev,next today', center: 'title', right: 'dayGridMonth,timeGridWeek,timeGridDay'},
        height: 'auto', firstDay: 1, nowIndicator: true, editable: true,
        eventDurationEditable: true, eventResizableFromStart: true,
        dayMaxEvents: true, allDayText: '종일', noEventsText: '일정이 없습니다.',
        eventTimeFormat: {hour: '2-digit', minute: '2-digit', hour12: false},
        slotLabelFormat: {hour: '2-digit', minute: '2-digit', hour12: false},
        events: this.events,
        dateClick: info => this.$emit('date_click', {start: info.dateStr, allDay: info.allDay}),
        eventClick: info => this.$emit('event_click', {id: info.event.id}),
        eventDrop: info => this.emitChange(info.event),
        eventResize: info => this.emitChange(info.event),
        datesSet: info => this.$emit('period_change', {start: info.startStr, end: info.endStr}),
      });
      this.calendar.render();
      // Tabs are initially hidden. Recalculate when a tab becomes visible or resizes.
      this.observer = new ResizeObserver(() => {
        cancelAnimationFrame(this.frame);
        this.frame = requestAnimationFrame(() => {
          if (this.$el.offsetWidth && this.calendar) this.calendar.updateSize();
        });
      });
      this.observer.observe(this.$el);
    } catch (error) {
      console.error('Calendar initialization failed', error);
      this.$el.textContent = '일정표를 불러오지 못했습니다. 페이지를 새로고침해 주세요.';
      this.$emit('load_error');
    }
  },
  beforeUnmount() {
    this.disposed = true;
    this.observer?.disconnect();
    cancelAnimationFrame(this.frame);
    this.calendar?.destroy();
    this.calendar = null;
  },
  methods: {
    emitChange(event) {
      this.calendar.setOption('editable', false);
      this.$emit('event_change', {id: event.id, start: event.startStr, end: event.endStr, allDay: event.allDay});
    },
    update_calendar() {
      if (!this.calendar) return;
      this.calendar.batchRendering(() => {
        this.calendar.removeAllEventSources();
        this.calendar.addEventSource(this.events);
        this.calendar.setOption('editable', true);
      });
    },
  },
};
