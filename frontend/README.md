# EcomStore Frontend

Professional e-commerce frontend built with React, TypeScript, and Vite. This frontend integrates seamlessly with the professional Django backend API.

## 🚀 Features

### ✨ **Professional UI/UX**
- Modern, responsive design with Tailwind CSS
- Mobile-first approach with smooth animations
- Professional color scheme and typography
- Accessibility-focused components

### 🔐 **Complete Authentication System**
- **Login & Registration** with form validation
- **JWT token management** with automatic refresh
- **Password strength indicator** and security features
- **Protected routes** for authenticated users
- **Role-based access control** (Admin/User)

### 🛍️ **Advanced Product Features**
- **Product browsing** with infinite scroll
- **Advanced filtering** by category, price, stock status
- **Search functionality** with real-time results
- **Product categories** with visual navigation
- **Featured products** highlighting
- **Responsive product grid** with hover effects

### 📱 **Responsive Design**
- **Mobile-optimized** interface
- **Tablet-friendly** layouts
- **Desktop-enhanced** experience
- **Touch-friendly** interactions

### ⚡ **Performance Optimized**
- **React Query** for efficient data fetching
- **Automatic caching** and background updates
- **Optimistic updates** for better UX
- **Code splitting** and lazy loading
- **Error boundaries** and retry logic

### 🎨 **Modern Tech Stack**
- **React 19** with TypeScript
- **Vite** for fast development
- **Tailwind CSS** for styling
- **React Query** for state management
- **React Router** for navigation
- **React Hook Form** for forms
- **Heroicons** for beautiful icons

## 🛠️ Tech Stack

- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: React Query + Context API
- **Routing**: React Router v6
- **Forms**: React Hook Form + Yup validation
- **HTTP Client**: Axios
- **Icons**: Heroicons
- **Notifications**: React Hot Toast

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ and npm
- Django backend running on `http://localhost:8000`

### Installation

1. **Install dependencies**:
```bash
npm install
```

2. **Start development server**:
```bash
npm run dev
```

3. **Access the application**:
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000/api`

## 📡 Backend Integration

### API Endpoints Used
- **Authentication**: `/api/auth/*`
  - Login, register, logout, profile management
  - JWT token refresh and validation
  - Password reset and email verification
- **Products**: `/api/products/*` and `/api/public/*`
  - Public product browsing (no auth required)
  - Admin product management (auth required)
  - Search, filtering, and pagination
- **Categories**: `/api/categories/*`
  - Category browsing and management

## 🎨 Design System

### Color Palette
- **Primary**: Blue (Tailwind blue-600)
- **Secondary**: Gray variants
- **Success**: Green (emerald-500)
- **Error**: Red (red-500)
- **Warning**: Yellow (yellow-500)

### Typography
- **Font**: Inter (Google Fonts)
- **Headings**: Bold weights (600-700)
- **Body**: Regular weight (400)

## 🔒 Security Features

- **JWT Token Management**: Secure storage and auto-refresh
- **Input Validation**: Client-side and server-side validation
- **Route Protection**: Role-based access control

## 📱 Mobile Experience

- **Responsive Design**: Works on all screen sizes
- **Touch Interactions**: Optimized for mobile devices
- **Fast Loading**: Optimized images and code splitting

---

**Built with ❤️ using modern React ecosystem and professional backend APIs**
