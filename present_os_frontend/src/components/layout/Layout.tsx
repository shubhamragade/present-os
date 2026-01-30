import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface LayoutProps {
    children: React.ReactNode;
}

export const Layout = ({ children }: LayoutProps) => {
    return (
        <div className="flex flex-col h-screen overflow-hidden bg-background font-sans text-white selection:bg-primary/20">
            <Header />

            <div className="flex flex-1 overflow-hidden relative">
                <main className="flex-1 flex flex-col relative z-0">
                    {children}
                </main>

                <Sidebar />
            </div>
        </div>
    );
};
