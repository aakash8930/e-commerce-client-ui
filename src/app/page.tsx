import ImageSlider from "@/components/ImageSlider";
import ProductList from "@/components/ProductList";

const Homepage = async ({
  searchParams,
}: {
  searchParams: Promise<{ category: string }>;
}) => {
  const category = (await searchParams).category;
  return (
    <div>
      <ImageSlider />
      <ProductList category={category} params="homepage" />
    </div>
  );
};

export default Homepage;
