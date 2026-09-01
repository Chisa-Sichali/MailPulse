export default function MainContainer({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <main className="flex flex-1 flex-col bg-background px-4 py-8 md:px-6 lg:px-16">
      {children}
    </main>
  );
}
