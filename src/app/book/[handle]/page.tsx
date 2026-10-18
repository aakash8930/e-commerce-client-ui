import BookingWizard from "@/components/booking/BookingWizard";

const BookPage = async ({
  params,
}: {
  params: Promise<{ handle: string }>;
}) => {
  const { handle } = await params;
  return <BookingWizard handle={handle} />;
};

export default BookPage;
