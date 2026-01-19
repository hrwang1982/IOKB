import { ThemeProvider } from '@/components/theme-provider';

export default function AuthLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
