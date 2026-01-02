export const BREAKPOINTS = {
	MOBILE: 320,
	TABLET: 768,
	DESKTOP: 1024
};

export const CHART_COLORS = [
	'#FF6B6B', // Red
	'#4ECDC4', // Teal
	'#45B7D1', // Blue
	'#FFA07A', // Light Salmon
	'#98D8C8', // Mint
	'#F7DC6F', // Yellow
	'#BB8FCE', // Purple
	'#F1948A', // Light Red
	'#D4A5A5', // Pinkish
	'#9B59B6', // Violet
	'#3498DB', // Dark Blue
	'#E67E22', // Orange
	'#2ECC71', // Green
	'#F1C40F', // Gold
	'#E74C3C', // Dark Red
	'#1ABC9C', // Dark Teal
	'#34495E'  // Dark Gray
];

export const getChartColor = (index) => {
	return CHART_COLORS[index % CHART_COLORS.length];
};
