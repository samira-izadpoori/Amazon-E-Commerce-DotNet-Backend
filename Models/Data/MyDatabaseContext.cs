using Microsoft.EntityFrameworkCore;
using ProductApi.Models;

namespace ProductApi.Data;

public class MyDatabaseContext : DbContext
{
    public MyDatabaseContext(
        DbContextOptions<MyDatabaseContext> options)
        : base(options)
    {
    }

    public DbSet<StoreProduct> StoreProducts { get; set; }

    public DbSet<Product> Products { get; set; }
}