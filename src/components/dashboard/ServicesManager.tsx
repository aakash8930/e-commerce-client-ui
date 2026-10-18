"use client";

import { SERVICE_COLORS } from "@/lib/seed";
import useAppStore from "@/lib/store";
import { formatMoney } from "@/lib/slots";
import {
  Service,
  ServiceFormInput,
  ServiceFormInputs,
  serviceFormSchema,
} from "@/lib/types";
import { zodResolver } from "@hookform/resolvers/zod";
import { Clock, Pencil, Plus, Trash2, X } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "react-toastify";

const durations = [15, 30, 45, 60, 90, 120];

const ServicesManager = () => {
  const { services, addService, updateService, deleteService, hasHydrated } =
    useAppStore();
  const [editing, setEditing] = useState<Service | null>(null);
  const [showForm, setShowForm] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<ServiceFormInput, unknown, ServiceFormInputs>({
    resolver: zodResolver(serviceFormSchema),
    defaultValues: {
      name: "",
      description: "",
      durationMin: 30,
      price: 0,
      color: SERVICE_COLORS[0],
    },
  });

  const selectedColor = watch("color");

  const openCreate = () => {
    setEditing(null);
    reset({
      name: "",
      description: "",
      durationMin: 30,
      price: 0,
      color: SERVICE_COLORS[0],
    });
    setShowForm(true);
  };

  const openEdit = (service: Service) => {
    setEditing(service);
    reset({
      name: service.name,
      description: service.description,
      durationMin: service.durationMin,
      price: service.price,
      color: service.color,
    });
    setShowForm(true);
  };

  const closeForm = () => {
    setShowForm(false);
    setEditing(null);
  };

  const onSubmit = (data: ServiceFormInputs) => {
    if (editing) {
      updateService(editing.id, data);
      toast.success("Service updated");
    } else {
      addService(data);
      toast.success("Service created");
    }
    closeForm();
  };

  const handleDelete = (service: Service) => {
    deleteService(service.id);
    toast.success(`Deleted “${service.name}”`);
  };

  if (!hasHydrated) {
    return <div className="h-64 animate-pulse rounded-2xl bg-gray-200" />;
  }

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Services</h1>
          <p className="mt-1 text-sm text-slate-500">
            What can clients book with you? Duration drives your slot length.
          </p>
        </div>
        {!showForm && (
          <button
            onClick={openCreate}
            className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" /> New service
          </button>
        )}
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="mt-6 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
        >
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900">
              {editing ? "Edit service" : "New service"}
            </h2>
            <button
              type="button"
              onClick={closeForm}
              className="rounded-lg p-1 text-slate-400 hover:bg-gray-50 hover:text-slate-600"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1 sm:col-span-2">
              <label htmlFor="name" className="text-xs font-medium text-slate-500">
                Name
              </label>
              <input
                id="name"
                placeholder="Strategy Call"
                className="rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-indigo-500"
                {...register("name")}
              />
              {errors.name && (
                <p className="text-xs text-red-500">{errors.name.message}</p>
              )}
            </div>
            <div className="flex flex-col gap-1 sm:col-span-2">
              <label htmlFor="description" className="text-xs font-medium text-slate-500">
                Description
              </label>
              <textarea
                id="description"
                rows={2}
                placeholder="What happens in this session?"
                className="rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-indigo-500"
                {...register("description")}
              />
              {errors.description && (
                <p className="text-xs text-red-500">
                  {errors.description.message}
                </p>
              )}
            </div>
            <div className="flex flex-col gap-1">
              <label htmlFor="durationMin" className="text-xs font-medium text-slate-500">
                Duration
              </label>
              <select
                id="durationMin"
                className="rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-indigo-500"
                {...register("durationMin")}
              >
                {durations.map((d) => (
                  <option key={d} value={d}>
                    {d} minutes
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label htmlFor="price" className="text-xs font-medium text-slate-500">
                Price (USD)
              </label>
              <input
                id="price"
                type="number"
                min={0}
                step="1"
                className="rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-indigo-500"
                {...register("price")}
              />
              {errors.price && (
                <p className="text-xs text-red-500">{errors.price.message}</p>
              )}
            </div>
            <div className="flex flex-col gap-2 sm:col-span-2">
              <span className="text-xs font-medium text-slate-500">Color</span>
              <div className="flex gap-2">
                {SERVICE_COLORS.map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => setValue("color", c)}
                    className={`h-7 w-7 rounded-full ${c} ${
                      selectedColor === c
                        ? "ring-2 ring-slate-900 ring-offset-2"
                        : ""
                    }`}
                    aria-label={`color ${c}`}
                  />
                ))}
              </div>
            </div>
          </div>

          <div className="mt-6 flex gap-3">
            <button
              type="submit"
              className="rounded-xl bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              {editing ? "Save changes" : "Create service"}
            </button>
            <button
              type="button"
              onClick={closeForm}
              className="rounded-xl border border-gray-300 px-5 py-2 text-sm font-medium text-slate-700 hover:border-slate-400"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {services.map((service) => (
          <div
            key={service.id}
            className="flex flex-col rounded-2xl border border-gray-200 bg-white p-5 shadow-sm"
          >
            <div className="flex items-start justify-between">
              <span className={`rounded-full px-2.5 py-1 text-xs font-medium text-white ${service.color}`}>
                {formatMoney(service.price)}
              </span>
              <div className="flex gap-1">
                <button
                  onClick={() => openEdit(service)}
                  className="rounded-lg p-1.5 text-slate-400 hover:bg-gray-50 hover:text-slate-700"
                  aria-label="Edit service"
                >
                  <Pencil className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDelete(service)}
                  className="rounded-lg p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
                  aria-label="Delete service"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
            <h3 className="mt-3 font-semibold text-slate-900">{service.name}</h3>
            <p className="mt-1 flex items-center gap-1 text-xs text-slate-500">
              <Clock className="h-3 w-3" /> {service.durationMin} min
            </p>
            <p className="mt-2 line-clamp-2 text-sm text-slate-600">
              {service.description}
            </p>
          </div>
        ))}
      </div>

      {services.length === 0 && (
        <p className="mt-6 rounded-2xl border border-dashed border-gray-300 p-8 text-center text-sm text-slate-500">
          No services yet — create your first one so clients can book it.
        </p>
      )}
    </div>
  );
};

export default ServicesManager;
