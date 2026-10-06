# Icons

Icons are optional. They need the npm packages `react`, `react-dom`, `react-icons`
and `sharp`; without them decks build without icons.

Use the exact name, case matters. Every name below was checked against react-icons 5.
A name that does not exist is replaced by `FaCheckCircle` and reported as a warning.

Supported prefixes: `Fa` (Font Awesome 5), `Md` (Material), `Hi` (Heroicons 1), `Bi` (BoxIcons), `Ri` (Remix), `Io` (Ionicons 5).
**Small models: use only `Fa` names from this page.** Full catalogue: https://react-icons.github.io/react-icons/

| Topic | Names |
|---|---|
| Growth, results | `FaChartLine` `FaChartBar` `FaChartPie` `FaArrowUp` `FaArrowDown` `FaTrophy` `FaAward` `FaMedal` `FaStar` `MdTrendingUp` `MdShowChart` |
| Money | `FaMoneyBillWave` `FaCoins` `FaWallet` `FaPiggyBank` `FaCreditCard` `FaUniversity` `MdAccountBalance` |
| People | `FaUsers` `FaUser` `FaHandshake` `FaComments` `FaHeart` `FaThumbsUp` `HiUsers` |
| Ideas, learning | `FaLightbulb` `FaBrain` `FaGraduationCap` `FaBookOpen` `FaQuestionCircle` `FaInfoCircle` `FaPuzzlePiece` |
| Goals, planning | `FaBullseye` `FaFlag` `FaRoute` `FaTasks` `FaClipboardList` `FaCalendarAlt` `FaClock` `FaStopwatch` `FaBalanceScale` |
| Technology | `FaLaptop` `FaMobileAlt` `FaCode` `FaServer` `FaDatabase` `FaCloud` `FaRobot` `FaCog` `FaCogs` `FaProjectDiagram` `FaLayerGroup` `FaSyncAlt` `MdDashboard` |
| Security, risk | `FaShieldAlt` `FaUserShield` `FaLock` `FaKey` `FaExclamationTriangle` `FaEye` `MdSecurity` |
| Speed, launch | `FaRocket` `FaBolt` |
| Business, places | `FaBuilding` `FaIndustry` `FaStore` `FaShoppingCart` `FaTruck` `FaHome` `FaGlobe` `FaMapMarkerAlt` `FaBullhorn` |
| Health | `FaHeartbeat` `FaHospital` |
| Environment | `FaLeaf` `FaSeedling` `FaRecycle` |
| Tools, search | `FaTools` `FaWrench` `FaSearch` `FaFilter` `FaFileAlt` `FaCamera` `FaEnvelope` `FaPhone` |
| Generic | `FaCheckCircle` |

## Colour

Cards and icon bullets accept `"color": "06B6D4"` (hex without `#`). Leave it out to use the theme accent.

## Emoji

A one to three character string such as `"★"` is drawn as text instead of an icon.
Emoji depend on the fonts of the viewer's computer, so prefer icon names.

## Automatic icons

`icon_grid` and `definition` cards and both sides of `two_column` get an icon chosen
from keywords in the header (English and Indonesian) when `icon` is missing.
