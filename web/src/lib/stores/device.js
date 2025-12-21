import { writable } from 'svelte/store';
import { BREAKPOINTS } from '$lib/constants';
import { browser } from '$app/environment';

function createDeviceStore() {
	const { subscribe, set } = writable({
		isMobile: false, // <= 320px
		isTablet: false, // <= 768px
		isDesktop: false, // > 768px
		width: 0
	});

	if (browser) {
		const update = () => {
			const width = window.innerWidth;
			set({
				isMobile: width <= BREAKPOINTS.MOBILE,
				isTablet: width <= BREAKPOINTS.TABLET,
				isDesktop: width > BREAKPOINTS.TABLET,
				width
			});
		};

		update();
		window.addEventListener('resize', update);
	}

	return { subscribe };
}

export const device = createDeviceStore();
